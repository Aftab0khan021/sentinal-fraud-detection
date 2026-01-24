"""
SentinAL: Audit Log Reporting & Verification Tool
=================================================
Generates compliance reports and verifies the cryptographic integrity of audit logs.

Usage:
    python audit_reports.py --report daily
    python audit_reports.py --verify

Author: SentinAL Security Team
Date: 2026-01-23
"""

import json
import argparse
import hmac
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# Constants
LOG_DIR = Path("logs/audit")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-prod").encode()

class LogVerifier:
    def __init__(self):
        pass

    def verify_signature(self, entry: Dict) -> bool:
        """Verify the HMAC signature of a log entry"""
        if "signature" not in entry:
            return False
            
        signature = entry.pop("signature")
        serialized = json.dumps(entry, sort_keys=True).encode()
        expected = hmac.new(SECRET_KEY, serialized, hashlib.sha256).hexdigest()
        
        # Put signature back
        entry["signature"] = signature
        return hmac.compare_digest(signature, expected)

    def scan_logs(self) -> Dict:
        """Scan all logs for tampering"""
        results = {"total": 0, "valid": 0, "tampered": 0, "errors": []}
        
        log_files = sorted(LOG_DIR.glob("*.jsonl*")) # Include rotated logs
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip(): continue
                        results["total"] += 1
                        try:
                            entry = json.loads(line)
                            if self.verify_signature(entry):
                                results["valid"] += 1
                            else:
                                results["tampered"] += 1
                                results["errors"].append(f"Tampered entry in {log_file.name}: {entry.get('timestamp')}")
                        except json.JSONDecodeError:
                            results["tampered"] += 1
                            results["errors"].append(f"Corrupt JSON in {log_file.name}")
            except Exception as e:
                results["errors"].append(f"Error reading {log_file.name}: {str(e)}")
                
        return results

def generate_report(days: int = 1):
    """Generate a summary report for the last N days"""
    verifier = LogVerifier()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    stats = {
        "fraud_detected": 0,
        "analyses_run": 0,
        "errors": 0,
        "users_analyzed": set()
    }
    
    print(f"\n{'='*60}")
    print(f"SENTINAL COMPLIANCE REPORT ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"{'='*60}")
    print(f"Period: Last {days} days\n")
    
    # Simple scan (in production would use index)
    log_files = sorted(LOG_DIR.glob("*.jsonl*"))
    
    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    
                    if ts.replace(tzinfo=None) < start_date:
                        continue
                        
                    if not verifier.verify_signature(entry.copy()):
                        print(f"!! WARNING: Tampered entry detected at {entry['timestamp']}")
                        continue
                        
                    event_type = entry.get('event_type')
                    details = entry.get('details', {})
                    
                    if event_type == "FRAUD_ANALYSIS":
                        stats["analyses_run"] += 1
                        stats["users_analyzed"].add(details.get("target_user_id"))
                        if details.get("is_fraud"):
                            stats["fraud_detected"] += 1
                            
                    if entry.get("status") == "ERROR":
                        stats["errors"] += 1
                        
                except Exception:
                    continue

    print(f"Total Analyses:     {stats['analyses_run']}")
    print(f"Unique Users:       {len(stats['users_analyzed'])}")
    print(f"Fraud Detected:     {stats['fraud_detected']} ({(stats['fraud_detected']/stats['analyses_run']*100 if stats['analyses_run'] else 0):.1f}%)")
    print(f"System Errors:      {stats['errors']}")
    print("-" * 60)
    print("End of Report")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Verify log integrity")
    parser.add_argument("--report", action="store_true", help="Generate activity report")
    parser.add_argument("--days", type=int, default=1, help="Days to include in report")
    
    args = parser.parse_args()
    
    if args.verify:
        verifier = LogVerifier()
        results = verifier.scan_logs()
        print(f"\nLog Verification Results:")
        print(f"Total Entries: {results['total']}")
        print(f"Valid:         {results['valid']}")
        print(f"Tampered:      {results['tampered']}")
        if results['errors']:
            print("\nErrors:")
            for err in results['errors']:
                print(f"  - {err}")
    elif args.report:
        generate_report(args.days)
    else:
        parser.print_help()
