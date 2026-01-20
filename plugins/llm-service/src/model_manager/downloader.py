"""
Model Downloader - Downloads models from HuggingFace Hub.
"""
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from huggingface_hub import (
        snapshot_download,
        hf_hub_download,
        model_info as get_model_info,
        list_files_info,
        HfApi,
    )
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("huggingface_hub not installed, model downloads disabled")


class DownloadStatus(str, Enum):
    """Status of a download task."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    """Progress information for a download."""
    model_id: str
    status: DownloadStatus
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    current_file: str = ""
    files_completed: int = 0
    files_total: int = 0
    speed_bytes_per_sec: float = 0.0
    eta_seconds: Optional[float] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class DownloadTask:
    """A model download task."""
    model_id: str
    revision: str = "main"
    local_dir: Optional[str] = None
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    token: Optional[str] = None
    force_download: bool = False
    
    # Runtime state
    status: DownloadStatus = DownloadStatus.PENDING
    progress: DownloadProgress = field(default_factory=lambda: DownloadProgress(
        model_id="", status=DownloadStatus.PENDING
    ))
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    def __post_init__(self):
        self.progress.model_id = self.model_id


class ModelDownloader:
    """
    Downloads models from HuggingFace Hub with progress tracking.
    
    Features:
    - Async download with progress callbacks
    - Cancellable downloads
    - Resume support (via HF Hub)
    - Include/exclude patterns for partial downloads
    - GGUF/GPTQ quantized model support
    """
    
    def __init__(
        self,
        cache_dir: str,
        token: Optional[str] = None,
        max_concurrent: int = 2
    ):
        if not HF_AVAILABLE:
            raise RuntimeError("huggingface_hub is required for model downloads")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token = token
        self.max_concurrent = max_concurrent
        self._api = HfApi(token=token)
        self._active_tasks: Dict[str, DownloadTask] = {}
        self._download_semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
    
    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a model from HuggingFace Hub."""
        try:
            info = await asyncio.to_thread(
                get_model_info,
                model_id,
                token=self.token
            )
            
            # Get file list
            files = await asyncio.to_thread(
                list,
                list_files_info(repo_id=model_id, token=self.token)
            )
            
            total_size = sum(f.size or 0 for f in files)
            
            return {
                "model_id": model_id,
                "author": info.author,
                "sha": info.sha,
                "last_modified": info.last_modified.isoformat() if info.last_modified else None,
                "private": info.private,
                "gated": info.gated,
                "downloads": info.downloads,
                "likes": info.likes,
                "tags": info.tags,
                "pipeline_tag": info.pipeline_tag,
                "library_name": info.library_name,
                "model_size_bytes": total_size,
                "model_size_gb": round(total_size / (1024**3), 2),
                "files_count": len(files),
                "files": [
                    {
                        "path": f.path,
                        "size": f.size,
                        "blob_id": f.blob_id,
                    }
                    for f in files[:50]  # Limit to first 50 files
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {e}")
            raise
    
    async def search_models(
        self,
        query: str,
        task: Optional[str] = None,
        library: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for models on HuggingFace Hub."""
        try:
            models = await asyncio.to_thread(
                self._api.list_models,
                search=query,
                task=task,
                library=library,
                limit=limit,
                sort="downloads",
                direction=-1
            )
            
            return [
                {
                    "model_id": m.id,
                    "author": m.author,
                    "downloads": m.downloads,
                    "likes": m.likes,
                    "pipeline_tag": m.pipeline_tag,
                    "tags": m.tags[:10] if m.tags else [],
                    "last_modified": m.last_modified.isoformat() if m.last_modified else None,
                }
                for m in models
            ]
        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            raise
    
    async def download(
        self,
        task: DownloadTask,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Path:
        """
        Download a model from HuggingFace Hub.
        
        Returns the local path where the model was downloaded.
        """
        async with self._download_semaphore:
            async with self._lock:
                self._active_tasks[task.model_id] = task
            
            task.status = DownloadStatus.DOWNLOADING
            task.progress.status = DownloadStatus.DOWNLOADING
            task.progress.started_at = datetime.utcnow().isoformat()
            
            try:
                # Determine local directory
                local_dir = task.local_dir or str(
                    self.cache_dir / task.model_id.replace("/", "--")
                )
                
                # Build download args
                download_kwargs = {
                    "repo_id": task.model_id,
                    "revision": task.revision,
                    "local_dir": local_dir,
                    "token": task.token or self.token,
                    "force_download": task.force_download,
                }
                
                if task.include_patterns:
                    download_kwargs["allow_patterns"] = task.include_patterns
                
                if task.exclude_patterns:
                    download_kwargs["ignore_patterns"] = task.exclude_patterns
                
                # Run download in thread pool
                logger.info(f"Starting download: {task.model_id} -> {local_dir}")
                
                # snapshot_download handles progress internally
                result_path = await asyncio.to_thread(
                    snapshot_download,
                    **download_kwargs
                )
                
                # Calculate total size
                total_size = sum(
                    f.stat().st_size 
                    for f in Path(result_path).rglob("*") 
                    if f.is_file()
                )
                
                # Update progress
                task.status = DownloadStatus.COMPLETED
                task.progress.status = DownloadStatus.COMPLETED
                task.progress.progress_percent = 100.0
                task.progress.downloaded_bytes = total_size
                task.progress.total_bytes = total_size
                task.progress.completed_at = datetime.utcnow().isoformat()
                
                if progress_callback:
                    progress_callback(task.progress)
                
                logger.info(f"Download completed: {task.model_id}")
                return Path(result_path)
                
            except Exception as e:
                task.status = DownloadStatus.FAILED
                task.progress.status = DownloadStatus.FAILED
                task.progress.error = str(e)
                logger.error(f"Download failed for {task.model_id}: {e}")
                
                if progress_callback:
                    progress_callback(task.progress)
                
                raise
            finally:
                async with self._lock:
                    self._active_tasks.pop(task.model_id, None)
    
    async def download_file(
        self,
        model_id: str,
        filename: str,
        revision: str = "main"
    ) -> Path:
        """Download a single file from a model repository."""
        try:
            local_path = await asyncio.to_thread(
                hf_hub_download,
                repo_id=model_id,
                filename=filename,
                revision=revision,
                token=self.token,
                local_dir=str(self.cache_dir / model_id.replace("/", "--"))
            )
            return Path(local_path)
        except Exception as e:
            logger.error(f"Failed to download {filename} from {model_id}: {e}")
            raise
    
    async def cancel(self, model_id: str) -> bool:
        """Cancel an active download."""
        async with self._lock:
            task = self._active_tasks.get(model_id)
            if task:
                task.cancel_event.set()
                task.status = DownloadStatus.CANCELLED
                task.progress.status = DownloadStatus.CANCELLED
                return True
            return False
    
    async def get_active_downloads(self) -> List[DownloadProgress]:
        """Get list of active downloads."""
        async with self._lock:
            return [task.progress for task in self._active_tasks.values()]
    
    async def delete_model(self, model_id: str) -> bool:
        """Delete a downloaded model from local cache."""
        local_path = self.cache_dir / model_id.replace("/", "--")
        if local_path.exists():
            try:
                shutil.rmtree(local_path)
                logger.info(f"Deleted model from cache: {model_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete model {model_id}: {e}")
                raise
        return False
    
    @staticmethod
    def get_recommended_patterns(model_type: str) -> Dict[str, List[str]]:
        """Get recommended include/exclude patterns for different model types."""
        patterns = {
            "gguf": {
                "include": ["*.gguf", "config.json", "tokenizer*"],
                "exclude": ["*.safetensors", "*.bin", "*.pt", "pytorch_model*"]
            },
            "gptq": {
                "include": ["*.safetensors", "config.json", "tokenizer*", "quantize_config.json"],
                "exclude": ["*.gguf", "*.bin"]
            },
            "awq": {
                "include": ["*.safetensors", "config.json", "tokenizer*", "quant_config.json"],
                "exclude": ["*.gguf", "*.bin"]
            },
            "safetensors": {
                "include": ["*.safetensors", "config.json", "tokenizer*", "generation_config.json"],
                "exclude": ["*.gguf", "pytorch_model*.bin"]
            },
            "full": {
                "include": [],
                "exclude": []
            }
        }
        return patterns.get(model_type, patterns["full"])
