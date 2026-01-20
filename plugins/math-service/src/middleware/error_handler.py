"""
Error handling middleware and utilities.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from datetime import datetime


async def http_exception_handler(request: Request, exc: Exception):
    """Handle HTTP exceptions."""
    status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', str(exc))
    
    logger.error(f"HTTP Exception: {status_code} - {detail}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{status_code}",
                "message": detail,
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )
