"""
SentinAL: Logging Tests
========================
Unit tests for logging configuration.

Author: SentinAL Testing Team
Date: 2026-01-23
"""

import pytest
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import hash_sensitive_data, setup_logging, get_logger


class TestLoggingFunctions:
    """Test suite for logging functions"""
    
    def test_hash_sensitive_data(self):
        """Test sensitive data hashing"""
        hash1 = hash_sensitive_data("12345")
        hash2 = hash_sensitive_data("12345")
        hash3 = hash_sensitive_data("67890")
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Different input should produce different hash
        assert hash1 != hash3
        
        # Hash should be 8 characters
        assert len(hash1) == 8
    
    def test_hash_different_types(self):
        """Test hashing different data types"""
        hash_int = hash_sensitive_data(123)
        hash_str = hash_sensitive_data("123")
        hash_float = hash_sensitive_data(123.0)
        
        # All should produce hashes
        assert len(hash_int) == 8
        assert len(hash_str) == 8
        assert len(hash_float) == 8
    
    def test_setup_logging(self):
        """Test logger setup"""
        logger = setup_logging()
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "sentinal"
    
    def test_get_logger(self):
        """Test getting logger instance"""
        logger = get_logger()
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_logger_has_handlers(self):
        """Test that logger has handlers configured"""
        logger = get_logger()
        
        # Should have at least one handler
        assert len(logger.handlers) > 0
