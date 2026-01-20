"""
Model Registry - Tracks locally available models.
"""
import json
import asyncio
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Status of a model in the registry."""
    DOWNLOADING = "downloading"
    READY = "ready"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    DELETED = "deleted"


@dataclass
class LocalModelInfo:
    """Information about a locally stored model."""
    model_id: str                    # HuggingFace model ID (e.g., "meta-llama/Llama-3.2-3B-Instruct")
    local_path: str                  # Path where model is stored
    status: ModelStatus = ModelStatus.READY
    size_bytes: int = 0              # Total size in bytes
    downloaded_at: Optional[str] = None
    last_used: Optional[str] = None
    revision: str = "main"           # Git revision/tag
    model_type: str = "unknown"      # causal-lm, seq2seq, embedding, etc.
    quantization: Optional[str] = None  # gguf, gptq, awq, etc.
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocalModelInfo":
        """Create from dictionary."""
        data = data.copy()
        data["status"] = ModelStatus(data.get("status", "ready"))
        return cls(**data)


class ModelRegistry:
    """
    Registry for managing locally downloaded models.
    
    Tracks model locations, status, and metadata.
    Persists to a JSON file for durability.
    """
    
    def __init__(self, cache_dir: str, registry_file: str = "model_registry.json"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.cache_dir / registry_file
        self._models: Dict[str, LocalModelInfo] = {}
        self._lock = asyncio.Lock()
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)
                    for model_id, info in data.get("models", {}).items():
                        self._models[model_id] = LocalModelInfo.from_dict(info)
                logger.info(f"Loaded {len(self._models)} models from registry")
            except Exception as e:
                logger.error(f"Failed to load model registry: {e}")
                self._models = {}
        else:
            self._models = {}
    
    def _save_registry(self) -> None:
        """Save registry to disk."""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.utcnow().isoformat(),
                "models": {
                    model_id: info.to_dict() 
                    for model_id, info in self._models.items()
                }
            }
            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
    
    async def register(self, model_info: LocalModelInfo) -> None:
        """Register a model in the registry."""
        async with self._lock:
            self._models[model_info.model_id] = model_info
            self._save_registry()
            logger.info(f"Registered model: {model_info.model_id}")
    
    async def update_status(
        self, 
        model_id: str, 
        status: ModelStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update model status."""
        async with self._lock:
            if model_id in self._models:
                self._models[model_id].status = status
                self._models[model_id].error_message = error_message
                if status == ModelStatus.LOADED:
                    self._models[model_id].last_used = datetime.utcnow().isoformat()
                self._save_registry()
    
    async def get(self, model_id: str) -> Optional[LocalModelInfo]:
        """Get model info by ID."""
        return self._models.get(model_id)
    
    async def list_models(
        self, 
        status: Optional[ModelStatus] = None,
        model_type: Optional[str] = None
    ) -> List[LocalModelInfo]:
        """List models, optionally filtered by status or type."""
        models = list(self._models.values())
        
        if status:
            models = [m for m in models if m.status == status]
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        return models
    
    async def remove(self, model_id: str) -> bool:
        """Remove model from registry (doesn't delete files)."""
        async with self._lock:
            if model_id in self._models:
                del self._models[model_id]
                self._save_registry()
                logger.info(f"Removed model from registry: {model_id}")
                return True
            return False
    
    async def exists(self, model_id: str) -> bool:
        """Check if model exists in registry."""
        return model_id in self._models
    
    async def get_model_path(self, model_id: str) -> Optional[Path]:
        """Get the local path for a model."""
        model = self._models.get(model_id)
        if model and model.status in (ModelStatus.READY, ModelStatus.LOADED):
            return Path(model.local_path)
        return None
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the model cache."""
        total_size = sum(m.size_bytes for m in self._models.values())
        
        return {
            "total_models": len(self._models),
            "ready_models": len([m for m in self._models.values() if m.status == ModelStatus.READY]),
            "loaded_models": len([m for m in self._models.values() if m.status == ModelStatus.LOADED]),
            "downloading": len([m for m in self._models.values() if m.status == ModelStatus.DOWNLOADING]),
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "cache_dir": str(self.cache_dir),
        }
    
    async def cleanup_failed(self) -> int:
        """Remove models with error status from registry."""
        async with self._lock:
            failed = [m for m in self._models.values() if m.status == ModelStatus.ERROR]
            for model in failed:
                del self._models[model.model_id]
            if failed:
                self._save_registry()
            return len(failed)
