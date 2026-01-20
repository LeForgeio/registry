"""
Health check routes.
"""
import time
from fastapi import APIRouter, Response
from datetime import datetime

router = APIRouter()

start_time = time.time()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "math-service",
        "version": "1.0.0",
        "uptime": int(time.time() - start_time),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/metrics")
async def metrics(response: Response):
    """Prometheus metrics endpoint."""
    uptime = time.time() - start_time
    
    metrics_text = f"""# HELP math_service_uptime_seconds Service uptime in seconds
# TYPE math_service_uptime_seconds gauge
math_service_uptime_seconds {uptime}

# HELP math_service_info Service information
# TYPE math_service_info gauge
math_service_info{{version="1.0.0"}} 1
"""
    
    response.headers["Content-Type"] = "text/plain"
    return Response(content=metrics_text, media_type="text/plain")
