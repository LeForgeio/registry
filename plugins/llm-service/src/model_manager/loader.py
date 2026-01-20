"""
Model Loader - Loads and manages model instances.
"""
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
import logging
import gc

logger = logging.getLogger(__name__)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        AutoConfig,
        BitsAndBytesConfig,
        pipeline,
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not installed, local model loading disabled")


class LoadedModel:
    """Wrapper for a loaded model instance."""
    
    def __init__(
        self,
        model_id: str,
        model: Any,
        tokenizer: Any,
        config: Any,
        device: str,
        dtype: str,
        loaded_at: str
    ):
        self.model_id = model_id
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.device = device
        self.dtype = dtype
        self.loaded_at = loaded_at
        self.last_used = loaded_at
        self.inference_count = 0
    
    def update_usage(self):
        """Update usage statistics."""
        self.last_used = datetime.utcnow().isoformat()
        self.inference_count += 1


class ModelLoader:
    """
    Loads and manages model instances for inference.
    
    Features:
    - Load models from local paths or HuggingFace Hub
    - Automatic device placement (CPU/CUDA)
    - Quantization support (4-bit, 8-bit)
    - Model caching with LRU eviction
    - Memory management
    """
    
    def __init__(
        self,
        cache_dir: str,
        max_loaded_models: int = 2,
        default_device: str = "auto",
        default_dtype: str = "auto"
    ):
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers is required for model loading")
        
        self.cache_dir = Path(cache_dir)
        self.max_loaded_models = max_loaded_models
        self.default_device = default_device
        self.default_dtype = default_dtype
        
        self._loaded_models: Dict[str, LoadedModel] = {}
        self._lock = asyncio.Lock()
        
        # Determine available device
        if TORCH_AVAILABLE and torch.cuda.is_available():
            self._available_device = "cuda"
            self._gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        else:
            self._available_device = "cpu"
            self._gpu_memory_gb = 0
    
    def _get_device(self, requested_device: str = "auto") -> str:
        """Determine the device to use."""
        if requested_device == "auto":
            return self._available_device
        return requested_device
    
    def _get_dtype(self, requested_dtype: str = "auto", device: str = "cpu"):
        """Determine the dtype to use."""
        if not TORCH_AVAILABLE:
            return None
            
        if requested_dtype == "auto":
            if device == "cuda":
                return torch.float16
            return torch.float32
        
        dtype_map = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        return dtype_map.get(requested_dtype, torch.float32)
    
    async def load(
        self,
        model_id: str,
        local_path: Optional[str] = None,
        device: str = "auto",
        dtype: str = "auto",
        quantization: Optional[str] = None,  # "4bit", "8bit", or None
        trust_remote_code: bool = False,
        max_memory: Optional[Dict] = None,
    ) -> LoadedModel:
        """
        Load a model for inference.
        
        Args:
            model_id: HuggingFace model ID or local identifier
            local_path: Path to local model files (optional)
            device: Device to load on ("auto", "cuda", "cpu")
            dtype: Data type ("auto", "float32", "float16", "bfloat16")
            quantization: Quantization mode ("4bit", "8bit", or None)
            trust_remote_code: Trust remote code in model
            max_memory: Max memory per device
        
        Returns:
            LoadedModel instance
        """
        async with self._lock:
            # Check if already loaded
            if model_id in self._loaded_models:
                logger.info(f"Model already loaded: {model_id}")
                return self._loaded_models[model_id]
            
            # Evict models if at capacity
            await self._evict_if_needed()
        
        # Determine source path
        model_path = local_path or model_id
        
        # Get device and dtype
        target_device = self._get_device(device)
        target_dtype = self._get_dtype(dtype, target_device)
        
        logger.info(f"Loading model: {model_id} on {target_device} with dtype {target_dtype}")
        
        try:
            # Build load kwargs
            load_kwargs: Dict[str, Any] = {
                "trust_remote_code": trust_remote_code,
            }
            
            if target_device == "cuda":
                load_kwargs["device_map"] = "auto"
                if max_memory:
                    load_kwargs["max_memory"] = max_memory
            
            if target_dtype:
                load_kwargs["torch_dtype"] = target_dtype
            
            # Configure quantization
            if quantization and TORCH_AVAILABLE:
                if quantization == "4bit":
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=target_dtype,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    )
                elif quantization == "8bit":
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_8bit=True,
                    )
            
            # Load config
            config = await asyncio.to_thread(
                AutoConfig.from_pretrained,
                model_path,
                trust_remote_code=trust_remote_code
            )
            
            # Determine model class
            model_class = AutoModelForCausalLM
            if hasattr(config, "is_encoder_decoder") and config.is_encoder_decoder:
                model_class = AutoModelForSeq2SeqLM
            
            # Load model
            model = await asyncio.to_thread(
                model_class.from_pretrained,
                model_path,
                **load_kwargs
            )
            
            # Load tokenizer
            tokenizer = await asyncio.to_thread(
                AutoTokenizer.from_pretrained,
                model_path,
                trust_remote_code=trust_remote_code
            )
            
            # Ensure tokenizer has pad token
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Move to device if not using device_map
            if target_device == "cpu" and hasattr(model, "to"):
                model = model.to(target_device)
            
            # Set to eval mode
            model.eval()
            
            # Create loaded model instance
            loaded = LoadedModel(
                model_id=model_id,
                model=model,
                tokenizer=tokenizer,
                config=config,
                device=target_device,
                dtype=str(target_dtype) if target_dtype else "default",
                loaded_at=datetime.utcnow().isoformat()
            )
            
            async with self._lock:
                self._loaded_models[model_id] = loaded
            
            logger.info(f"Model loaded successfully: {model_id}")
            return loaded
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise
    
    async def unload(self, model_id: str) -> bool:
        """Unload a model and free memory."""
        async with self._lock:
            if model_id not in self._loaded_models:
                return False
            
            loaded = self._loaded_models.pop(model_id)
            
            # Delete model and tokenizer
            del loaded.model
            del loaded.tokenizer
            del loaded.config
            
            # Force garbage collection
            gc.collect()
            
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Model unloaded: {model_id}")
            return True
    
    async def _evict_if_needed(self) -> None:
        """Evict least recently used model if at capacity."""
        while len(self._loaded_models) >= self.max_loaded_models:
            # Find LRU model
            lru_model = min(
                self._loaded_models.values(),
                key=lambda m: m.last_used
            )
            logger.info(f"Evicting LRU model: {lru_model.model_id}")
            await self.unload(lru_model.model_id)
    
    async def get(self, model_id: str) -> Optional[LoadedModel]:
        """Get a loaded model by ID."""
        return self._loaded_models.get(model_id)
    
    async def is_loaded(self, model_id: str) -> bool:
        """Check if a model is loaded."""
        return model_id in self._loaded_models
    
    async def list_loaded(self) -> list:
        """List all loaded models."""
        return [
            {
                "model_id": m.model_id,
                "device": m.device,
                "dtype": m.dtype,
                "loaded_at": m.loaded_at,
                "last_used": m.last_used,
                "inference_count": m.inference_count,
            }
            for m in self._loaded_models.values()
        ]
    
    async def generate(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True,
        **kwargs
    ) -> str:
        """Generate text using a loaded model."""
        loaded = self._loaded_models.get(model_id)
        if not loaded:
            raise ValueError(f"Model not loaded: {model_id}")
        
        loaded.update_usage()
        
        # Tokenize input
        inputs = loaded.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        
        # Move to model device
        if TORCH_AVAILABLE:
            device = next(loaded.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "do_sample": do_sample,
            "pad_token_id": loaded.tokenizer.pad_token_id,
            "eos_token_id": loaded.tokenizer.eos_token_id,
            **kwargs
        }
        
        with torch.no_grad() if TORCH_AVAILABLE else nullcontext():
            outputs = await asyncio.to_thread(
                loaded.model.generate,
                **inputs,
                **generation_kwargs
            )
        
        # Decode output (only new tokens)
        input_length = inputs["input_ids"].shape[1]
        generated = outputs[0][input_length:]
        text = loaded.tokenizer.decode(generated, skip_special_tokens=True)
        
        return text
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage."""
        result = {
            "loaded_models": len(self._loaded_models),
            "max_loaded_models": self.max_loaded_models,
        }
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            result["gpu"] = {
                "total_gb": self._gpu_memory_gb,
                "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
                "reserved_gb": torch.cuda.memory_reserved() / (1024**3),
            }
        
        return result


# Context manager fallback for when torch is not available
class nullcontext:
    def __enter__(self):
        return None
    def __exit__(self, *args):
        pass
