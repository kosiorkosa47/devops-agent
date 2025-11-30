"""
Redis connection and caching
"""
import logging
from typing import Optional
from redis.asyncio import Redis, ConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[Redis] = None
redis_pool: Optional[ConnectionPool] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client, redis_pool
    
    try:
        redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True
        )
        redis_client = Redis(connection_pool=redis_pool)
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis initialized successfully")
        
    except Exception as e:
        logger.error(f"Redis initialization error: {e}", exc_info=True)
        raise


async def close_redis():
    """Close Redis connection"""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
    if redis_pool:
        await redis_pool.disconnect()
    
    logger.info("Redis connection closed")


async def get_redis_client() -> Redis:
    """Get Redis client"""
    if redis_client is None:
        raise RuntimeError("Redis not initialized")
    return redis_client
