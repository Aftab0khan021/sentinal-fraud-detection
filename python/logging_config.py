"""
SentinAL: Logging Configuration
================================
Structured logging with file rotation and sensitive data protection.

Author: SentinAL Security Team
Date: 2026-01-23
"""

import os
import logging
import hashlib
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "api.log")
LOG_MAX_SIZE_MB = int(os.getenv("LOG_MAX_SIZE_MB", "10"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))


def hash_sensitive_data(data: any) -> str:
    """
    Hash sensitive data for secure logging.
    
    Args:
        data: Any data to hash (will be converted to string)
        
    Returns:
        First 8 characters of SHA256 hash
        
    Example:
        >>> hash_sensitive_data(12345)
        'e3b0c442'
    """
    data_str = str(data)
    return hashlib.sha256(data_str.encode()).hexdigest()[:8]


def setup_logging():
    """
    Configure logging with file rotation and console output.
    
    Creates two handlers:
    1. Console handler for immediate feedback
    2. Rotating file handler for persistent logs
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("sentinal")
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Format for log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_SIZE_MB * 1024 * 1024,  # Convert MB to bytes
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging configured: level={LOG_LEVEL}, file={LOG_FILE}")
    
    return logger


def get_logger(name: str = "sentinal") -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (default: "sentinal")
        
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger()
        >>> logger.info("Application started")
    """
    return logging.getLogger(name)


# Initialize logging on module import
logger = setup_logging()
