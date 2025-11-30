"""
Simple runner for DevOps Agent Backend - for quick testing
Runs without Prometheus and database requirements
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DevOps Agent API",
    description="AI-Powered DevOps Agent with Claude",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

# Dummy user for testing (no auth)
@app.get("/api/users/me")
async def get_current_user():
    return {"user_id": "test-user", "username": "test"}

@app.post("/api/users/login")
async def login():
    return {"token": "test-token", "user_id": "test-user"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "simple"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting DevOps Agent Backend (Simple Mode)")
    logger.info(f"🤖 Claude Model: {settings.CLAUDE_MODEL}")
    logger.info("📡 Server will be available at: http://localhost:8000")
    logger.info("📚 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
