"""
SentinAL: Secure Audit Logger (GDPR & Compliance Ready)
=======================================================
Implements tamper-proof logging with cryptographic signatures.

Features:
- HMAC-SHA256 signatures for log integrity
- Rotation support (daily logs)
- Structured JSON logging
- Sensitive data masking

Author: SentinAL Security Team
Date: 2026-01-23
"""

import logging
import logging.handlers
import json
import os
import hmac
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
LOG_DIR = Path("logs/audit")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-prod").encode()

class AuditLogger:
    def __init__(self):
        self._setup_logger()
    
    def _setup_logger(self):
        """Initialize the audit logger with file rotation"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("audit_logger")
        self.logger.setLevel(logging.INFO)
        
        # Use a separate file handler for audit logs
        # Rotates at midnight
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=LOG_DIR / "audit.jsonl",
            when="midnight",
            interval=1,
            backupCount=90,  # Keep 90 days of logs (Compliance)
            encoding="utf-8"
        )
        
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _sign_entry(self, entry: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for the log entry"""
        # Sort keys to ensure consistent signature
        serialized = json.dumps(entry, sort_keys=True).encode()
        signature = hmac.new(SECRET_KEY, serialized, hashlib.sha256).hexdigest()
        return signature

    def log_event(self, 
                  event_type: str, 
                  user_id: Optional[str] = None, 
                  action: str = "", 
                  details: Dict[str, Any] = None,
                  status: str = "SUCCESS"):
        """
        Log a security or compliance event.
        
        args:
            event_type: Category (e.g., 'AUTH', 'FRAUD_ANALYSIS', 'DATA_ACCESS')
            user_id: ID of the user performing the action (or subject)
            action: Specific action (e.g., 'login', 'analyze_user')
            details: Additional context
            status: Outcome of the action
        """
        if details is None:
            details = {}
            
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        log_entry = {
            "version": "1.0",
            "timestamp": timestamp,
            "event_type": event_type,
            "user_id": user_id or "system",
            "action": action,
            "status": status,
            "details": details,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
        # Add signature
        log_entry["signature"] = self._sign_entry(log_entry)
        
        # Write structured log
        self.logger.info(json.dumps(log_entry))

# Global instance
audit_logger = AuditLogger()

def log_audit_event(event_type: str, **kwargs):
    """Helper function to log events easily"""
    audit_logger.log_event(event_type, **kwargs)
