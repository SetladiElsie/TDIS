"""Caching utilities using Redis"""

import redis
import json
import pickle
from datetime import timedelta
from functools import wraps
from logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Redis cache manager"""
    
    def __init__(self, redis_url='redis://localhost:6379/0'):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory cache.")
            self.redis_client = None
            self._memory_cache = {}
    
    def get(self, key):
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {str(e)}")
        return None
    
    def set(self, key, value, expire=3600):
        """Set value in cache"""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    expire,
                    json.dumps(value, default=str)
                )
            else:
                self._memory_cache[key] = value
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {str(e)}")
            return False
    
    def delete(self, key):
        """Delete from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {str(e)}")
            return False
    
    def clear(self, pattern=None):
        """Clear cache"""
        try:
            if self.redis_client:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
            else:
                if pattern:
                    self._memory_cache = {
                        k: v for k, v in self._memory_cache.items()
                        if pattern not in k
                    }
                else:
                    self._memory_cache.clear()
            return True
        except Exception as e:
            logger.warning(f"Cache clear failed: {str(e)}")
            return False
    
    def exists(self, key):
        """Check if key exists"""
        try:
            if self.redis_client:
                return self.redis_client.exists(key) > 0
            else:
                return key in self._memory_cache
        except Exception as e:
            logger.warning(f"Cache exists check failed: {str(e)}")
            return False
    
    def incr(self, key, amount=1):
        """Increment counter"""
        try:
            if self.redis_client:
                return self.redis_client.incr(key, amount)
            else:
                self._memory_cache[key] = self._memory_cache.get(key, 0) + amount
                return self._memory_cache[key]
        except Exception as e:
            logger.warning(f"Cache incr failed: {str(e)}")
            return 0
    
    def mget(self, keys):
        """Get multiple values"""
        try:
            if self.redis_client:
                values = self.redis_client.mget(keys)
                return [json.loads(v) if v else None for v in values]
            else:
                return [self._memory_cache.get(k) for k in keys]
        except Exception as e:
            logger.warning(f"Cache mget failed: {str(e)}")
            return [None] * len(keys)
    
    def mset(self, data, expire=3600):
        """Set multiple values"""
        try:
            if self.redis_client:
                pipe = self.redis_client.pipeline()
                for key, value in data.items():
                    pipe.setex(key, expire, json.dumps(value, default=str))
                pipe.execute()
            else:
                self._memory_cache.update(data)
            return True
        except Exception as e:
            logger.warning(f"Cache mset failed: {str(e)}")
            return False


def cache_result(key_prefix, expire=3600):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache = CacheManager()
            
            # Build cache key
            cache_key = f"{key_prefix}:{args}:{kwargs}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, expire)
            
            return result
        
        return decorated_function
    
    return decorator


def invalidate_cache(pattern):
    """Invalidate cache by pattern"""
    cache = CacheManager()
    cache.clear(pattern)


# Global cache instance
cache = CacheManager()


# Cache operations for specific data types

def cache_extraction_result(extraction_id, data, expire=86400):  # 24 hours
    """Cache extraction result"""
    cache.set(f"extraction:{extraction_id}", data, expire)


def get_cached_extraction_result(extraction_id):
    """Get cached extraction result"""
    return cache.get(f"extraction:{extraction_id}")


def invalidate_extraction_cache(extraction_id):
    """Invalidate extraction cache"""
    cache.delete(f"extraction:{extraction_id}")


def cache_user_uploads(user_id, data, expire=3600):
    """Cache user uploads list"""
    cache.set(f"user_uploads:{user_id}", data, expire)


def get_cached_user_uploads(user_id):
    """Get cached user uploads"""
    return cache.get(f"user_uploads:{user_id}")


def invalidate_user_cache(user_id):
    """Invalidate user cache"""
    cache.clear(f"user_uploads:{user_id}*")


def cache_search_results(search_key, results, expire=1800):  # 30 minutes
    """Cache search results"""
    cache.set(f"search:{search_key}", results, expire)


def get_cached_search_results(search_key):
    """Get cached search results"""
    return cache.get(f"search:{search_key}")


def invalidate_search_cache():
    """Invalidate all search cache"""
    cache.clear("search:*")
