"""
SentinAL: Distributed Cache Manager
====================================
Centralized caching with Redis and automatic fallback to in-memory cache.

Features:
- Redis connection pooling
- Automatic fallback to in-memory LRU cache
- TTL (Time-To-Live) management
- JSON serialization
- Health check monitoring

Author: SentinAL Team
Date: 2026-01-24
"""

import json
import logging
import os
from typing import Optional, Any, Dict
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Redis, but don't fail if unavailable
try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Falling back to in-memory cache.")


class CacheManager:
    """
    Centralized cache manager with Redis and in-memory fallback.
    """
    
    def __init__(self):
        self.redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        self.redis_client = None
        self.fallback_cache = {}  # Simple dict for fallback
        
        if REDIS_AVAILABLE and self.redis_enabled:
            self._init_redis()
        else:
            logger.info("Using in-memory cache (Redis disabled or unavailable)")
    
    def _init_redis(self):
        """Initialize Redis connection with pooling."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD", None)
            
            # Create connection pool
            pool = ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password if redis_password else None,
                decode_responses=True,
                max_connections=10,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"✓ Connected to Redis at {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return value
                logger.debug(f"Cache MISS (Redis): {key}")
                return None
            else:
                # Fallback to in-memory
                value = self.fallback_cache.get(key)
                if value:
                    logger.debug(f"Cache HIT (Memory): {key}")
                else:
                    logger.debug(f"Cache MISS (Memory): {key}")
                return value
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, value)
                logger.debug(f"Cache SET (Redis): {key} [TTL: {ttl}s]")
            else:
                # Fallback to in-memory (no TTL support in simple dict)
                self.fallback_cache[key] = value
                logger.debug(f"Cache SET (Memory): {key}")
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    def delete(self, key: str):
        """Delete key from cache."""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
                logger.debug(f"Cache DELETE (Redis): {key}")
            else:
                self.fallback_cache.pop(key, None)
                logger.debug(f"Cache DELETE (Memory): {key}")
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    def clear_pattern(self, pattern: str):
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "fraud_explanation:*")
        """
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} keys matching pattern: {pattern}")
            else:
                # Fallback: clear all keys starting with pattern prefix
                prefix = pattern.replace("*", "")
                keys_to_delete = [k for k in self.fallback_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.fallback_cache[key]
                logger.info(f"Cleared {len(keys_to_delete)} keys from memory cache")
                
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check cache health and return statistics.
        
        Returns:
            Dictionary with health status and stats
        """
        health = {
            "cache_type": "redis" if self.redis_client else "memory",
            "redis_available": REDIS_AVAILABLE,
            "redis_enabled": self.redis_enabled,
            "status": "unknown"
        }
        
        try:
            if self.redis_client:
                # Test Redis connection
                self.redis_client.ping()
                info = self.redis_client.info("stats")
                
                health["status"] = "healthy"
                health["redis_version"] = self.redis_client.info("server").get("redis_version")
                health["total_keys"] = self.redis_client.dbsize()
                health["hits"] = info.get("keyspace_hits", 0)
                health["misses"] = info.get("keyspace_misses", 0)
                
                total = health["hits"] + health["misses"]
                health["hit_rate"] = f"{(health['hits'] / total * 100):.2f}%" if total > 0 else "N/A"
                
            else:
                health["status"] = "healthy"
                health["total_keys"] = len(self.fallback_cache)
                health["note"] = "Using in-memory fallback cache"
                
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            logger.error(f"Cache health check failed: {e}")
        
        return health


# Global cache manager instance
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return cache_manager
