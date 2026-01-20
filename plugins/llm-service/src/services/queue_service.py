"""
Redis Queue Service for managing LLM request queues.
"""
import asyncio
import json
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from loguru import logger

from ..config import settings


class RequestStatus(str, Enum):
    """Status of a queued request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueuedRequest:
    """A request in the queue."""
    id: str
    endpoint: str
    payload: Dict[str, Any]
    status: RequestStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QueuedRequest":
        data["status"] = RequestStatus(data["status"])
        return cls(**data)


class QueueService:
    """
    Redis-based queue service for managing LLM requests.
    Provides request queuing, status tracking, and result retrieval.
    """

    def __init__(self):
        self.redis_url = settings.redis_url
        self.queue_name = settings.redis_queue_name
        self.enabled = settings.enable_queue
        self._redis: Optional[redis.Redis] = None
        self._processing = False
        self._worker_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            logger.info("Queue service is disabled")
            return

        try:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    async def enqueue(
        self,
        request_id: str,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> QueuedRequest:
        """
        Add a request to the queue.

        Args:
            request_id: Unique request ID
            endpoint: API endpoint
            payload: Request payload

        Returns:
            QueuedRequest object
        """
        if not self.enabled or not self._redis:
            raise RuntimeError("Queue service is not enabled or connected")

        request = QueuedRequest(
            id=request_id,
            endpoint=endpoint,
            payload=payload,
            status=RequestStatus.PENDING,
            created_at=time.time(),
        )

        # Store request data
        await self._redis.hset(
            f"request:{request_id}",
            mapping={
                "data": json.dumps(request.to_dict()),
            }
        )

        # Add to queue
        await self._redis.lpush(self.queue_name, request_id)

        logger.debug(f"Enqueued request {request_id} for {endpoint}")
        return request

    async def get_request(self, request_id: str) -> Optional[QueuedRequest]:
        """Get a request by ID."""
        if not self._redis:
            return None

        data = await self._redis.hget(f"request:{request_id}", "data")
        if not data:
            return None

        return QueuedRequest.from_dict(json.loads(data))

    async def update_request(self, request: QueuedRequest):
        """Update a request in storage."""
        if not self._redis:
            return

        await self._redis.hset(
            f"request:{request.id}",
            mapping={
                "data": json.dumps(request.to_dict()),
            }
        )

    async def get_queue_length(self) -> int:
        """Get the number of pending requests."""
        if not self._redis:
            return 0
        return await self._redis.llen(self.queue_name)

    async def get_processing_count(self) -> int:
        """Get the number of requests being processed."""
        if not self._redis:
            return 0

        # Count requests with PROCESSING status
        keys = await self._redis.keys("request:*")
        count = 0
        for key in keys:
            data = await self._redis.hget(key, "data")
            if data:
                req = json.loads(data)
                if req.get("status") == RequestStatus.PROCESSING.value:
                    count += 1
        return count

    async def start_worker(
        self,
        handler: Callable[[QueuedRequest], Any],
    ):
        """
        Start the queue worker.

        Args:
            handler: Async function to process requests
        """
        if not self.enabled or not self._redis:
            logger.warning("Cannot start worker: queue not enabled or connected")
            return

        self._processing = True
        self._worker_task = asyncio.create_task(
            self._worker_loop(handler)
        )
        logger.info("Queue worker started")

    async def stop_worker(self):
        """Stop the queue worker."""
        self._processing = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        logger.info("Queue worker stopped")

    async def _worker_loop(
        self,
        handler: Callable[[QueuedRequest], Any],
    ):
        """Main worker loop."""
        while self._processing:
            try:
                # Block waiting for a request (with timeout)
                result = await self._redis.brpop(self.queue_name, timeout=1)
                if not result:
                    continue

                _, request_id = result
                request = await self.get_request(request_id)
                if not request:
                    continue

                # Update status to processing
                request.status = RequestStatus.PROCESSING
                request.started_at = time.time()
                await self.update_request(request)

                try:
                    # Process the request
                    result = await handler(request)
                    request.result = result
                    request.status = RequestStatus.COMPLETED
                except Exception as e:
                    logger.error(f"Request {request_id} failed: {e}")
                    request.error = str(e)
                    request.status = RequestStatus.FAILED

                request.completed_at = time.time()
                await self.update_request(request)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def get_status(self) -> dict:
        """Get queue status."""
        return {
            "enabled": self.enabled,
            "connected": self._redis is not None,
            "pending_requests": await self.get_queue_length(),
            "processing_requests": await self.get_processing_count(),
            "queue_name": self.queue_name,
        }

    async def clear_queue(self):
        """Clear all pending requests from the queue."""
        if not self._redis:
            return

        await self._redis.delete(self.queue_name)
        logger.info("Queue cleared")


# Singleton instance
_queue_service: Optional[QueueService] = None


def get_queue_service() -> QueueService:
    """Get or create the queue service singleton."""
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service
