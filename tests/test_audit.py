import unittest
import os
import shutil
import json
from pathlib import Path
from python.audit_logger import AuditLogger, log_audit_event
from python.audit_reports import LogVerifier

class TestAuditLogging(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory for logs
        self.test_log_dir = Path("logs/test_audit")
        if self.test_log_dir.exists():
            shutil.rmtree(self.test_log_dir)
        self.test_log_dir.mkdir(parents=True)
        
        # Patch the LOG_DIR in the modules
        import python.audit_logger
        python.audit_logger.LOG_DIR = self.test_log_dir
        
        import python.audit_reports
        python.audit_reports.LOG_DIR = self.test_log_dir
        
        # Re-initialize logger
        self.logger = AuditLogger()
        python.audit_logger.audit_logger = self.logger

    def tearDown(self):
        # Close handlers to release file locks (Windows fix)
        if hasattr(self, 'logger') and hasattr(self.logger, 'logger'):
            for handler in self.logger.logger.handlers[:]:
                handler.close()
                self.logger.logger.removeHandler(handler)
        
        # Cleanup
        if self.test_log_dir.exists():
            try:
                shutil.rmtree(self.test_log_dir)
            except OSError:
                # Ignore cleanup errors on Windows if file is still transiently locked
                pass

    def test_log_creation(self):
        """Test that log file is created and contains valid JSON"""
        self.logger.log_event("TEST_EVENT", "user_123", "test_action", {"foo": "bar"})
        
        log_file = self.test_log_dir / "audit.jsonl"
        self.assertTrue(log_file.exists())
        
        with open(log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)
            self.assertEqual(entry['event_type'], 'TEST_EVENT')
            self.assertEqual(entry['user_id'], 'user_123')
            self.assertTrue('signature' in entry)

    def test_signature_verification(self):
        """Test that signatures are verified correctly"""
        self.logger.log_event("VALID_EVENT", "user_1", "valid")
        
        verifier = LogVerifier()
        results = verifier.scan_logs()
        self.assertEqual(results['valid'], 1)
        self.assertEqual(results['tampered'], 0)

    def test_tamper_detection(self):
        """Test that modified logs are detected as tampered"""
        self.logger.log_event("SENSITIVE_EVENT", "admin", "access")
        
        log_file = self.test_log_dir / "audit.jsonl"
        
        # Manually tamper with the file
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        entry = json.loads(lines[0])
        entry['user_id'] = "hacker" # Change data without updating signature
        
        with open(log_file, 'w') as f:
            f.write(json.dumps(entry) + "\n")
            
        # Verify
        verifier = LogVerifier()
        results = verifier.scan_logs()
        self.assertEqual(results['valid'], 0)
        self.assertEqual(results['tampered'], 1)

if __name__ == '__main__':
    unittest.main()
