"""
Health check endpoints
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import engine
from app.core.redis import get_redis_client
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    database: str
    redis: str
    claude_api: str


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies
    Returns 200 if service is ready to handle requests
    """
    return {"status": "ready"}


@router.get("/health/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    Detailed health check with all dependencies
    """
    health_status = {
        "status": "healthy",
        "version": settings.API_VERSION,
        "database": "unknown",
        "redis": "unknown",
        "claude_api": "unknown"
    }
    
    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis = await get_redis_client()
        await redis.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Claude API (just verify key is set)
    if settings.ANTHROPIC_API_KEY:
        health_status["claude_api"] = "configured"
    else:
        health_status["claude_api"] = "not_configured"
        health_status["status"] = "degraded"
    
    if health_status["status"] == "degraded":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint (served by prometheus_client)
    This endpoint is handled by the metrics middleware
    """
    return {"message": "Use /metrics endpoint for Prometheus metrics"}
