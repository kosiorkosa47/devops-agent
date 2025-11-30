"""
DevOps Agent Backend - Main Application
FastAPI backend with Claude API integration
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.config import settings
from app.api.routes import chat, health, users
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events"""
    # Startup
    logger.info("Starting DevOps Agent Backend...")
    try:
        await init_db()
        logger.info("Database connected")
    except Exception as e:
        logger.warning(f"Database connection failed (optional): {e}")
    
    try:
        await init_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed (optional): {e}")
    
    logger.info("Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        await close_db()
        await close_redis()
    except Exception:
        pass
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="DevOps Agent API",
    description="AI-powered DevOps agent with Claude integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# Agent router (NEW - agentic execution)
from app.api.routes import agent
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
