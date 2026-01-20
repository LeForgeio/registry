"""
Model Manager - High-level API for model management.

Combines registry, downloader, and loader for a unified interface.
"""
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from .registry import ModelRegistry, LocalModelInfo, ModelStatus
from .downloader import ModelDownloader, DownloadTask, DownloadProgress, DownloadStatus
from .loader import ModelLoader, LoadedModel

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Unified interface for model management.
    
    Handles:
    - Model discovery and search
    - Downloading models from HuggingFace
    - Local model registry
    - Loading/unloading models for inference
    - Hot-swapping models at runtime
    """
    
    def __init__(
        self,
        cache_dir: str,
        hf_token: Optional[str] = None,
        max_loaded_models: int = 2,
        max_concurrent_downloads: int = 2,
        default_device: str = "auto",
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.registry = ModelRegistry(str(self.cache_dir))
        self.downloader = ModelDownloader(
            str(self.cache_dir),
            token=hf_token,
            max_concurrent=max_concurrent_downloads
        )
        self.loader = ModelLoader(
            str(self.cache_dir),
            max_loaded_models=max_loaded_models,
            default_device=default_device
        )
        
        self._download_callbacks: Dict[str, List[callable]] = {}
    
    # =========================================================================
    # Model Discovery
    # =========================================================================
    
    async def search_models(
        self,
        query: str,
        task: Optional[str] = None,
        library: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query
            task: Filter by task (text-generation, text-classification, etc.)
            library: Filter by library (transformers, diffusers, etc.)
            limit: Maximum results to return
        
        Returns:
            List of model info dictionaries
        """
        return await self.downloader.search_models(query, task, library, limit)
    
    async def get_remote_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a model from HuggingFace Hub."""
        info = await self.downloader.get_model_info(model_id)
        
        # Check local status
        local_model = await self.registry.get(model_id)
        if local_model:
            info["local_status"] = local_model.status.value
            info["local_path"] = local_model.local_path
            info["is_downloaded"] = local_model.status in (ModelStatus.READY, ModelStatus.LOADED)
            info["is_loaded"] = local_model.status == ModelStatus.LOADED
        else:
            info["local_status"] = None
            info["is_downloaded"] = False
            info["is_loaded"] = False
        
        return info
    
    # =========================================================================
    # Model Downloads
    # =========================================================================
    
    async def download_model(
        self,
        model_id: str,
        revision: str = "main",
        quantization: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        force: bool = False
    ) -> LocalModelInfo:
        """
        Download a model from HuggingFace Hub.
        
        Args:
            model_id: HuggingFace model ID
            revision: Git revision/branch/tag
            quantization: Quantization type (gguf, gptq, awq, safetensors, full)
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            force: Force re-download even if exists
        
        Returns:
            LocalModelInfo for the downloaded model
        """
        # Check if already downloaded
        existing = await self.registry.get(model_id)
        if existing and existing.status == ModelStatus.READY and not force:
            logger.info(f"Model already downloaded: {model_id}")
            return existing
        
        # Get recommended patterns for quantization type
        if quantization and not include_patterns and not exclude_patterns:
            patterns = ModelDownloader.get_recommended_patterns(quantization)
            include_patterns = patterns.get("include", [])
            exclude_patterns = patterns.get("exclude", [])
        
        # Create download task
        task = DownloadTask(
            model_id=model_id,
            revision=revision,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
            force_download=force,
        )
        
        # Register as downloading
        model_info = LocalModelInfo(
            model_id=model_id,
            local_path="",
            status=ModelStatus.DOWNLOADING,
            revision=revision,
            quantization=quantization,
        )
        await self.registry.register(model_info)
        
        try:
            # Execute download
            local_path = await self.downloader.download(
                task,
                progress_callback=lambda p: self._handle_progress(model_id, p)
            )
            
            # Get model info from HuggingFace
            try:
                remote_info = await self.downloader.get_model_info(model_id)
                model_type = remote_info.get("pipeline_tag", "unknown")
            except:
                model_type = "unknown"
            
            # Calculate size
            total_size = sum(
                f.stat().st_size 
                for f in local_path.rglob("*") 
                if f.is_file()
            )
            
            # Update registry
            model_info = LocalModelInfo(
                model_id=model_id,
                local_path=str(local_path),
                status=ModelStatus.READY,
                size_bytes=total_size,
                downloaded_at=datetime.utcnow().isoformat(),
                revision=revision,
                model_type=model_type,
                quantization=quantization,
            )
            await self.registry.register(model_info)
            
            logger.info(f"Model downloaded: {model_id} -> {local_path}")
            return model_info
            
        except Exception as e:
            await self.registry.update_status(
                model_id, 
                ModelStatus.ERROR,
                error_message=str(e)
            )
            raise
    
    def _handle_progress(self, model_id: str, progress: DownloadProgress):
        """Handle download progress updates."""
        callbacks = self._download_callbacks.get(model_id, [])
        for callback in callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    async def cancel_download(self, model_id: str) -> bool:
        """Cancel an in-progress download."""
        cancelled = await self.downloader.cancel(model_id)
        if cancelled:
            await self.registry.update_status(model_id, ModelStatus.ERROR, "Cancelled")
        return cancelled
    
    async def get_download_progress(self) -> List[DownloadProgress]:
        """Get progress of active downloads."""
        return await self.downloader.get_active_downloads()
    
    # =========================================================================
    # Local Model Management
    # =========================================================================
    
    async def list_local_models(
        self,
        status: Optional[str] = None,
        model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List locally available models.
        
        Args:
            status: Filter by status (ready, loaded, downloading, error)
            model_type: Filter by model type
        
        Returns:
            List of model info dictionaries
        """
        status_filter = ModelStatus(status) if status else None
        models = await self.registry.list_models(status_filter, model_type)
        return [m.to_dict() for m in models]
    
    async def get_local_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a local model."""
        model = await self.registry.get(model_id)
        if model:
            return model.to_dict()
        return None
    
    async def delete_model(self, model_id: str, delete_files: bool = True) -> bool:
        """
        Delete a model from local cache.
        
        Args:
            model_id: Model to delete
            delete_files: Also delete the model files
        
        Returns:
            True if deleted successfully
        """
        # Unload if loaded
        if await self.loader.is_loaded(model_id):
            await self.loader.unload(model_id)
        
        # Delete files
        if delete_files:
            await self.downloader.delete_model(model_id)
        
        # Remove from registry
        return await self.registry.remove(model_id)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the model cache."""
        return await self.registry.get_cache_stats()
    
    # =========================================================================
    # Model Loading
    # =========================================================================
    
    async def load_model(
        self,
        model_id: str,
        device: str = "auto",
        dtype: str = "auto",
        quantization: Optional[str] = None,
        trust_remote_code: bool = False
    ) -> Dict[str, Any]:
        """
        Load a model for inference.
        
        If not downloaded, will download first.
        
        Args:
            model_id: Model to load
            device: Device to load on
            dtype: Data type to use
            quantization: Runtime quantization (4bit, 8bit)
            trust_remote_code: Trust remote code
        
        Returns:
            Info about the loaded model
        """
        # Check if downloaded
        local_model = await self.registry.get(model_id)
        if not local_model or local_model.status not in (ModelStatus.READY, ModelStatus.LOADED):
            # Download first
            logger.info(f"Model not downloaded, downloading: {model_id}")
            local_model = await self.download_model(model_id)
        
        # Update status
        await self.registry.update_status(model_id, ModelStatus.LOADING)
        
        try:
            # Load the model
            loaded = await self.loader.load(
                model_id=model_id,
                local_path=local_model.local_path,
                device=device,
                dtype=dtype,
                quantization=quantization,
                trust_remote_code=trust_remote_code
            )
            
            # Update status
            await self.registry.update_status(model_id, ModelStatus.LOADED)
            
            return {
                "model_id": loaded.model_id,
                "device": loaded.device,
                "dtype": loaded.dtype,
                "loaded_at": loaded.loaded_at,
                "local_path": local_model.local_path,
            }
            
        except Exception as e:
            await self.registry.update_status(
                model_id,
                ModelStatus.READY,  # Revert to ready, not error
                error_message=str(e)
            )
            raise
    
    async def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        result = await self.loader.unload(model_id)
        if result:
            await self.registry.update_status(model_id, ModelStatus.READY)
        return result
    
    async def list_loaded_models(self) -> List[Dict[str, Any]]:
        """List currently loaded models."""
        return await self.loader.list_loaded()
    
    async def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is currently loaded."""
        return await self.loader.is_loaded(model_id)
    
    # =========================================================================
    # Inference
    # =========================================================================
    
    async def generate(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        Generate text using a model.
        
        Will load the model if not already loaded.
        
        Args:
            model_id: Model to use
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text
        """
        # Ensure model is loaded
        if not await self.loader.is_loaded(model_id):
            await self.load_model(model_id)
        
        return await self.loader.generate(
            model_id=model_id,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs
        )
    
    # =========================================================================
    # Hot-swap
    # =========================================================================
    
    async def hot_swap(
        self,
        current_model: str,
        new_model: str,
        device: str = "auto",
        dtype: str = "auto",
        quantization: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hot-swap one model for another.
        
        Unloads the current model and loads the new one.
        
        Args:
            current_model: Model to unload
            new_model: Model to load
            device: Device for new model
            dtype: Dtype for new model
            quantization: Quantization for new model
        
        Returns:
            Info about the newly loaded model
        """
        logger.info(f"Hot-swapping {current_model} -> {new_model}")
        
        # Unload current
        await self.unload_model(current_model)
        
        # Load new
        return await self.load_model(
            new_model,
            device=device,
            dtype=dtype,
            quantization=quantization
        )
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return await self.loader.get_memory_usage()
