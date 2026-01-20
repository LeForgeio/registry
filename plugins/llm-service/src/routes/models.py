"""
Model Management Routes - BYOM (Bring Your Own Model) API.

Endpoints for:
- Searching HuggingFace models
- Downloading models
- Managing local model cache
- Loading/unloading models
- Hot-swapping models
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..config import get_settings
from ..model_manager import ModelManager, ModelStatus

router = APIRouter(prefix="/models", tags=["Model Management"])

# Global model manager instance
_manager: Optional[ModelManager] = None


def get_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _manager
    if _manager is None:
        settings = get_settings()
        _manager = ModelManager(
            cache_dir=settings.model_cache_dir,
            hf_token=settings.huggingface_api_key,
            max_loaded_models=2,
            default_device="auto"
        )
    return _manager


# =============================================================================
# Request/Response Models
# =============================================================================

class SearchRequest(BaseModel):
    """Search request for HuggingFace models."""
    query: str = Field(..., description="Search query")
    task: Optional[str] = Field(None, description="Filter by task (text-generation, etc.)")
    library: Optional[str] = Field(None, description="Filter by library (transformers, etc.)")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class DownloadRequest(BaseModel):
    """Request to download a model."""
    model_id: str = Field(..., description="HuggingFace model ID")
    revision: str = Field("main", description="Git revision/branch/tag")
    quantization: Optional[str] = Field(
        None, 
        description="Quantization type: gguf, gptq, awq, safetensors, full"
    )
    include_patterns: Optional[List[str]] = Field(
        None, 
        description="File patterns to include"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None, 
        description="File patterns to exclude"
    )
    force: bool = Field(False, description="Force re-download")


class LoadRequest(BaseModel):
    """Request to load a model."""
    model_id: str = Field(..., description="Model to load")
    device: str = Field("auto", description="Device: auto, cuda, cpu")
    dtype: str = Field("auto", description="Data type: auto, float32, float16, bfloat16")
    quantization: Optional[str] = Field(
        None, 
        description="Runtime quantization: 4bit, 8bit"
    )
    trust_remote_code: bool = Field(False, description="Trust remote code")


class HotSwapRequest(BaseModel):
    """Request to hot-swap models."""
    current_model: str = Field(..., description="Model to unload")
    new_model: str = Field(..., description="Model to load")
    device: str = Field("auto", description="Device for new model")
    dtype: str = Field("auto", description="Data type for new model")
    quantization: Optional[str] = Field(None, description="Quantization for new model")


class GenerateRequest(BaseModel):
    """Request to generate text with a specific model."""
    model_id: str = Field(..., description="Model to use")
    prompt: str = Field(..., description="Input prompt")
    max_new_tokens: int = Field(512, ge=1, le=4096, description="Max tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling")
    top_k: int = Field(50, ge=1, description="Top-k sampling")
    do_sample: bool = Field(True, description="Use sampling (vs greedy)")


class DeleteRequest(BaseModel):
    """Request to delete a model."""
    model_id: str = Field(..., description="Model to delete")
    delete_files: bool = Field(True, description="Also delete model files")


# =============================================================================
# Search & Discovery Endpoints
# =============================================================================

@router.post("/search")
async def search_models(request: SearchRequest):
    """
    Search for models on HuggingFace Hub.
    
    Returns list of models matching the query with metadata.
    """
    manager = get_manager()
    try:
        results = await manager.search_models(
            query=request.query,
            task=request.task,
            library=request.library,
            limit=request.limit
        )
        return {
            "query": request.query,
            "count": len(results),
            "models": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{model_id:path}")
async def get_model_info(model_id: str):
    """
    Get detailed information about a model.
    
    Fetches from HuggingFace Hub and includes local status.
    """
    manager = get_manager()
    try:
        return await manager.get_remote_model_info(model_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {e}")


# =============================================================================
# Download Endpoints
# =============================================================================

@router.post("/download")
async def download_model(
    request: DownloadRequest,
    background_tasks: BackgroundTasks
):
    """
    Download a model from HuggingFace Hub.
    
    Downloads asynchronously. Check status with /local/{model_id}.
    
    Quantization patterns:
    - gguf: Downloads only GGUF quantized files
    - gptq: Downloads GPTQ quantized weights
    - awq: Downloads AWQ quantized weights
    - safetensors: Downloads safetensors format
    - full: Downloads everything (default)
    """
    manager = get_manager()
    
    # Check if already downloaded
    existing = await manager.get_local_model(request.model_id)
    if existing and existing.get("status") == "ready" and not request.force:
        return {
            "status": "already_downloaded",
            "model": existing
        }
    
    # Start download in background
    async def do_download():
        try:
            await manager.download_model(
                model_id=request.model_id,
                revision=request.revision,
                quantization=request.quantization,
                include_patterns=request.include_patterns,
                exclude_patterns=request.exclude_patterns,
                force=request.force
            )
        except Exception as e:
            # Error is stored in registry
            pass
    
    background_tasks.add_task(do_download)
    
    return {
        "status": "downloading",
        "model_id": request.model_id,
        "message": "Download started. Check status with GET /models/local/{model_id}"
    }


@router.post("/download/cancel/{model_id:path}")
async def cancel_download(model_id: str):
    """Cancel an in-progress download."""
    manager = get_manager()
    cancelled = await manager.cancel_download(model_id)
    return {
        "model_id": model_id,
        "cancelled": cancelled
    }


@router.get("/download/progress")
async def get_download_progress():
    """Get progress of all active downloads."""
    manager = get_manager()
    progress = await manager.get_download_progress()
    return {
        "active_downloads": len(progress),
        "downloads": [
            {
                "model_id": p.model_id,
                "status": p.status.value,
                "progress_percent": p.progress_percent,
                "downloaded_bytes": p.downloaded_bytes,
                "total_bytes": p.total_bytes,
                "current_file": p.current_file,
                "error": p.error,
            }
            for p in progress
        ]
    }


# =============================================================================
# Local Model Management
# =============================================================================

@router.get("/local")
async def list_local_models(
    status: Optional[str] = None,
    model_type: Optional[str] = None
):
    """
    List locally available models.
    
    Query params:
    - status: Filter by status (ready, loaded, downloading, error)
    - model_type: Filter by model type
    """
    manager = get_manager()
    models = await manager.list_local_models(status=status, model_type=model_type)
    return {
        "count": len(models),
        "models": models
    }


@router.get("/local/{model_id:path}")
async def get_local_model(model_id: str):
    """Get information about a specific local model."""
    manager = get_manager()
    model = await manager.get_local_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    return model


@router.delete("/local/{model_id:path}")
async def delete_local_model(model_id: str, delete_files: bool = True):
    """
    Delete a model from local cache.
    
    Query params:
    - delete_files: Also delete model files (default: true)
    """
    manager = get_manager()
    deleted = await manager.delete_model(model_id, delete_files=delete_files)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    return {
        "model_id": model_id,
        "deleted": True,
        "files_deleted": delete_files
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """Get statistics about the model cache."""
    manager = get_manager()
    return await manager.get_cache_stats()


# =============================================================================
# Model Loading
# =============================================================================

@router.post("/load")
async def load_model(request: LoadRequest):
    """
    Load a model for inference.
    
    Will download the model first if not already downloaded.
    Limited to 2 models loaded at once (configurable).
    LRU eviction when at capacity.
    """
    manager = get_manager()
    try:
        result = await manager.load_model(
            model_id=request.model_id,
            device=request.device,
            dtype=request.dtype,
            quantization=request.quantization,
            trust_remote_code=request.trust_remote_code
        )
        return {
            "status": "loaded",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unload/{model_id:path}")
async def unload_model(model_id: str):
    """Unload a model from memory."""
    manager = get_manager()
    unloaded = await manager.unload_model(model_id)
    if not unloaded:
        raise HTTPException(status_code=404, detail=f"Model not loaded: {model_id}")
    return {
        "model_id": model_id,
        "unloaded": True
    }


@router.get("/loaded")
async def list_loaded_models():
    """List currently loaded models."""
    manager = get_manager()
    models = await manager.list_loaded_models()
    return {
        "count": len(models),
        "models": models
    }


@router.get("/loaded/{model_id:path}")
async def check_model_loaded(model_id: str):
    """Check if a specific model is loaded."""
    manager = get_manager()
    is_loaded = await manager.is_model_loaded(model_id)
    return {
        "model_id": model_id,
        "is_loaded": is_loaded
    }


# =============================================================================
# Hot-swap
# =============================================================================

@router.post("/hot-swap")
async def hot_swap_model(request: HotSwapRequest):
    """
    Hot-swap one model for another.
    
    Unloads the current model and loads the new one.
    Useful for switching models without restarting the service.
    """
    manager = get_manager()
    try:
        result = await manager.hot_swap(
            current_model=request.current_model,
            new_model=request.new_model,
            device=request.device,
            dtype=request.dtype,
            quantization=request.quantization
        )
        return {
            "status": "swapped",
            "unloaded": request.current_model,
            "loaded": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Direct Generation
# =============================================================================

@router.post("/generate")
async def generate_with_model(request: GenerateRequest):
    """
    Generate text using a specific model.
    
    Will load the model if not already loaded.
    """
    manager = get_manager()
    try:
        text = await manager.generate(
            model_id=request.model_id,
            prompt=request.prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            do_sample=request.do_sample
        )
        return {
            "model_id": request.model_id,
            "generated_text": text,
            "prompt_length": len(request.prompt),
            "generated_length": len(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Memory
# =============================================================================

@router.get("/memory")
async def get_memory_usage():
    """Get memory usage statistics."""
    manager = get_manager()
    return await manager.get_memory_usage()


# =============================================================================
# Recommended Models
# =============================================================================

@router.get("/recommended")
async def get_recommended_models():
    """
    Get a curated list of recommended models for common tasks.
    """
    return {
        "text_generation": {
            "small": [
                {"model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "size_gb": 2.2, "description": "Fast, lightweight chat model"},
                {"model_id": "microsoft/phi-2", "size_gb": 5.5, "description": "Strong reasoning in small package"},
            ],
            "medium": [
                {"model_id": "mistralai/Mistral-7B-Instruct-v0.2", "size_gb": 14, "description": "Excellent quality/size balance"},
                {"model_id": "meta-llama/Llama-3.2-3B-Instruct", "size_gb": 6, "description": "Latest Llama, very capable"},
            ],
            "large": [
                {"model_id": "meta-llama/Llama-3.1-8B-Instruct", "size_gb": 16, "description": "Flagship open model"},
                {"model_id": "Qwen/Qwen2.5-7B-Instruct", "size_gb": 14, "description": "Strong multilingual support"},
            ],
        },
        "code_generation": [
            {"model_id": "codellama/CodeLlama-7b-Instruct-hf", "size_gb": 14, "description": "Code-specialized Llama"},
            {"model_id": "deepseek-ai/deepseek-coder-6.7b-instruct", "size_gb": 13, "description": "Strong code understanding"},
        ],
        "embeddings": [
            {"model_id": "BAAI/bge-small-en-v1.5", "size_gb": 0.13, "description": "Fast, high quality embeddings"},
            {"model_id": "sentence-transformers/all-MiniLM-L6-v2", "size_gb": 0.09, "description": "Popular, well-rounded"},
        ],
        "quantized_gguf": [
            {"model_id": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF", "size_gb": 4, "description": "Q4_K_M quantized"},
            {"model_id": "TheBloke/Llama-2-7B-Chat-GGUF", "size_gb": 4, "description": "Q4_K_M quantized"},
        ],
    }
