"""
Tests for Cache Manager
========================
Tests Redis caching functionality with fallback to in-memory cache.

Author: SentinAL Team
Date: 2026-01-24
"""

import unittest
import os
import time
from unittest.mock import patch, MagicMock
import sys

# Add python directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

from cache_manager import CacheManager


class TestCacheManager(unittest.TestCase):
    """Test suite for CacheManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Force in-memory cache for tests
        os.environ['REDIS_ENABLED'] = 'false'
        self.cache = CacheManager()
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.cache, 'fallback_cache'):
            self.cache.fallback_cache.clear()
    
    def test_cache_initialization(self):
        """Test cache manager initializes correctly"""
        self.assertIsNotNone(self.cache)
        self.assertFalse(self.cache.redis_enabled or self.cache.redis_client is not None)
    
    def test_cache_set_and_get(self):
        """Test basic set and get operations"""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value)
        retrieved = self.cache.get(key)
        
        self.assertEqual(retrieved, value)
    
    def test_cache_get_nonexistent(self):
        """Test getting non-existent key returns None"""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)
    
    def test_cache_delete(self):
        """Test cache deletion"""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value)
        self.assertEqual(self.cache.get(key), value)
        
        self.cache.delete(key)
        self.assertIsNone(self.cache.get(key))
    
    def test_cache_clear_pattern(self):
        """Test pattern-based cache clearing"""
        # Set multiple keys
        self.cache.set("fraud_explanation:1", "explanation 1")
        self.cache.set("fraud_explanation:2", "explanation 2")
        self.cache.set("other_key", "other value")
        
        # Clear pattern
        self.cache.clear_pattern("fraud_explanation:*")
        
        # Check that pattern keys are cleared but others remain
        self.assertIsNone(self.cache.get("fraud_explanation:1"))
        self.assertIsNone(self.cache.get("fraud_explanation:2"))
        self.assertEqual(self.cache.get("other_key"), "other value")
    
    def test_health_check(self):
        """Test health check returns valid status"""
        health = self.cache.health_check()
        
        self.assertIn("status", health)
        self.assertIn("cache_type", health)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["cache_type"], "memory")
    
    def test_cache_with_ttl(self):
        """Test that TTL parameter is accepted (actual expiration not tested in memory cache)"""
        key = "ttl_key"
        value = "ttl_value"
        
        # Should not raise error
        self.cache.set(key, value, ttl=60)
        self.assertEqual(self.cache.get(key), value)
    
    def test_multiple_operations(self):
        """Test multiple cache operations"""
        # Set multiple values
        for i in range(10):
            self.cache.set(f"key_{i}", f"value_{i}")
        
        # Verify all values
        for i in range(10):
            self.assertEqual(self.cache.get(f"key_{i}"), f"value_{i}")
        
        # Delete half
        for i in range(0, 10, 2):
            self.cache.delete(f"key_{i}")
        
        # Verify deletions
        for i in range(10):
            if i % 2 == 0:
                self.assertIsNone(self.cache.get(f"key_{i}"))
            else:
                self.assertEqual(self.cache.get(f"key_{i}"), f"value_{i}")


class TestCacheManagerWithRedis(unittest.TestCase):
    """Test suite for CacheManager with Redis (mocked)"""
    
    def setUp(self):
        """Check if Redis is available"""
        try:
            import redis
            self.redis_available = True
        except ImportError:
            self.redis_available = False
    
    def test_redis_initialization(self):
        """Test Redis initialization when available"""
        if not self.redis_available:
            self.skipTest("Redis not installed")
        
        from unittest.mock import patch, MagicMock
        
        with patch('cache_manager.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis.ping.return_value = True
            mock_redis_class.return_value = mock_redis
            
            os.environ['REDIS_ENABLED'] = 'true'
            os.environ['REDIS_HOST'] = 'localhost'
            os.environ['REDIS_PORT'] = '6379'
            
            cache = CacheManager()
            
            self.assertIsNotNone(cache.redis_client)
            mock_redis.ping.assert_called_once()
    
    def test_redis_get_set(self):
        """Test Redis get/set operations"""
        if not self.redis_available:
            self.skipTest("Redis not installed")
        
        from unittest.mock import patch, MagicMock
        
        with patch('cache_manager.redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis.ping.return_value = True
            mock_redis.get.return_value = "cached_value"
            mock_redis_class.return_value = mock_redis
            
            os.environ['REDIS_ENABLED'] = 'true'
            cache = CacheManager()
            
            # Test set
            cache.set("test_key", "test_value", ttl=3600)
            mock_redis.setex.assert_called_once_with("test_key", 3600, "test_value")
            
            # Test get
            result = cache.get("test_key")
            self.assertEqual(result, "cached_value")
            mock_redis.get.assert_called_once_with("test_key")


if __name__ == '__main__':
    unittest.main()
