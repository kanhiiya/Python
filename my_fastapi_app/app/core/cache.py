"""Redis caching utility for FastAPI application.

Provides a simple caching layer using Redis with JSON serialization.
Falls back to no-caching when Redis is unavailable.
"""

import json
import logging
from typing import Any, Optional, Union
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with graceful fallback."""
    
    def __init__(self):
        self.redis = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection if REDIS_URL is configured."""
        redis_url = getattr(settings, "REDIS_URL", None)
        if redis_url:
            try:
                import aioredis
                self.redis = aioredis.from_url(
                    redis_url, 
                    encoding="utf-8", 
                    decode_responses=True
                )
                logger.info("Cache service initialized with Redis")
            except Exception as exc:
                logger.warning("Failed to initialize Redis cache: %s", exc)
        else:
            logger.info("No REDIS_URL configured, caching disabled")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache by key."""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as exc:
            logger.warning("Cache get error for key '%s': %s", key, exc)
        
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire_seconds: int = 300
    ) -> bool:
        """Set value in cache with optional expiration."""
        if not self.redis:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, expire_seconds, serialized)
            return True
        except Exception as exc:
            logger.warning("Cache set error for key '%s': %s", key, exc)
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as exc:
            logger.warning("Cache delete error for key '%s': %s", key, exc)
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern (e.g., 'items:*')."""
        if not self.redis:
            return False
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as exc:
            logger.warning("Cache delete pattern error for '%s': %s", pattern, exc)
            return False


# Global cache instance
cache_service = CacheService()