"""
Fraud Pattern Library and Rule Engine
======================================
Provides rule-based fraud pattern detection and pattern management.

Features:
- Pre-defined fraud patterns
- Custom pattern builder
- Rule engine
- Pattern analytics
- Integration with ML model

Author: SentinAL Team
Date: 2026-01-24
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Operator(Enum):
    """Comparison operators for rules"""

    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    MATCHES = "matches"


class Severity(Enum):
    """Pattern severity levels"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Rule:
    """Single rule in a pattern"""

    field: str
    operator: Operator
    value: Any
    description: str = ""

    def evaluate(self, data: Dict[str, Any]) -> bool:
        """
        Evaluate rule against data.

        Args:
            data: Data dictionary

        Returns:
            True if rule matches
        """
        if self.field not in data:
            return False

        field_value = data[self.field]

        try:
            if self.operator == Operator.EQUALS:
                return field_value == self.value
            elif self.operator == Operator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == Operator.GREATER_THAN:
                return field_value > self.value
            elif self.operator == Operator.LESS_THAN:
                return field_value < self.value
            elif self.operator == Operator.GREATER_EQUAL:
                return field_value >= self.value
            elif self.operator == Operator.LESS_EQUAL:
                return field_value <= self.value
            elif self.operator == Operator.IN:
                return field_value in self.value
            elif self.operator == Operator.NOT_IN:
                return field_value not in self.value
            elif self.operator == Operator.CONTAINS:
                return self.value in field_value
            elif self.operator == Operator.MATCHES:
                import re

                return bool(re.match(self.value, str(field_value)))
            else:
                return False
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return False


@dataclass
class FraudPattern:
    """Fraud pattern definition"""

    id: str
    name: str
    description: str
    rules: List[Rule]
    severity: Severity
    category: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, data: Dict[str, Any], require_all: bool = True) -> bool:
        """
        Check if data matches this pattern.

        Args:
            data: Data to check
            require_all: If True, all rules must match (AND). If False, any rule matches (OR)

        Returns:
            True if pattern matches
        """
        if not self.enabled:
            return False

        if not self.rules:
            return False

        results = [rule.evaluate(data) for rule in self.rules]

        if require_all:
            return all(results)
        else:
            return any(results)


class PatternLibrary:
    """
    Library of fraud patterns with rule engine.
    """

    def __init__(self):
        self.patterns: Dict[str, FraudPattern] = {}
        self._load_default_patterns()

    def _load_default_patterns(self):
        """Load pre-defined fraud patterns"""

        # Pattern 1: Rapid Transactions
        self.add_pattern(
            FraudPattern(
                id="rapid_transactions",
                name="Rapid Transactions",
                description="Multiple transactions in a short time window",
                rules=[
                    Rule(
                        "transaction_count", Operator.GREATER_THAN, 10, "More than 10 transactions"
                    ),
                    Rule("time_window_seconds", Operator.LESS_THAN, 60, "Within 60 seconds"),
                ],
                severity=Severity.HIGH,
                category="velocity",
            )
        )

        # Pattern 2: Circular Money Flow
        self.add_pattern(
            FraudPattern(
                id="circular_flow",
                name="Circular Money Flow",
                description="Money returns to source through intermediaries",
                rules=[
                    Rule(
                        "path_length",
                        Operator.GREATER_THAN,
                        3,
                        "Transaction path longer than 3 hops",
                    ),
                    Rule(
                        "returns_to_source",
                        Operator.EQUALS,
                        True,
                        "Money returns to original sender",
                    ),
                ],
                severity=Severity.CRITICAL,
                category="money_laundering",
            )
        )

        # Pattern 3: Unusual Transaction Amount
        self.add_pattern(
            FraudPattern(
                id="unusual_amount",
                name="Unusual Transaction Amount",
                description="Transaction amount significantly different from user's history",
                rules=[
                    Rule(
                        "amount_deviation",
                        Operator.GREATER_THAN,
                        3.0,
                        "Amount is 3+ standard deviations from mean",
                    )
                ],
                severity=Severity.MEDIUM,
                category="anomaly",
            )
        )

        # Pattern 4: Geographic Anomaly
        self.add_pattern(
            FraudPattern(
                id="geographic_anomaly",
                name="Geographic Anomaly",
                description="Transaction from unusual location",
                rules=[
                    Rule(
                        "distance_from_usual_km",
                        Operator.GREATER_THAN,
                        1000,
                        "More than 1000km from usual location",
                    ),
                    Rule(
                        "time_since_last_transaction_hours",
                        Operator.LESS_THAN,
                        2,
                        "Less than 2 hours since last transaction",
                    ),
                ],
                severity=Severity.HIGH,
                category="location",
            )
        )

        # Pattern 5: Structuring (Smurfing)
        self.add_pattern(
            FraudPattern(
                id="structuring",
                name="Structuring/Smurfing",
                description="Multiple transactions just below reporting threshold",
                rules=[
                    Rule("transaction_count", Operator.GREATER_THAN, 5, "More than 5 transactions"),
                    Rule(
                        "all_below_threshold",
                        Operator.EQUALS,
                        True,
                        "All amounts just below $10,000",
                    ),
                    Rule("time_window_hours", Operator.LESS_THAN, 24, "Within 24 hours"),
                ],
                severity=Severity.CRITICAL,
                category="money_laundering",
            )
        )

        # Pattern 6: Account Takeover
        self.add_pattern(
            FraudPattern(
                id="account_takeover",
                name="Account Takeover",
                description="Suspicious account access pattern",
                rules=[
                    Rule(
                        "failed_login_attempts",
                        Operator.GREATER_THAN,
                        5,
                        "More than 5 failed logins",
                    ),
                    Rule("new_device", Operator.EQUALS, True, "Login from new device"),
                    Rule("new_location", Operator.EQUALS, True, "Login from new location"),
                ],
                severity=Severity.CRITICAL,
                category="account_security",
            )
        )

        # Pattern 7: Mule Account
        self.add_pattern(
            FraudPattern(
                id="mule_account",
                name="Money Mule Account",
                description="Account used as intermediary for money laundering",
                rules=[
                    Rule(
                        "rapid_in_out", Operator.EQUALS, True, "Money received and sent out quickly"
                    ),
                    Rule(
                        "account_age_days",
                        Operator.LESS_THAN,
                        30,
                        "New account (less than 30 days)",
                    ),
                    Rule(
                        "transaction_volume",
                        Operator.GREATER_THAN,
                        50000,
                        "High transaction volume",
                    ),
                ],
                severity=Severity.HIGH,
                category="money_laundering",
            )
        )

        # Pattern 8: Synthetic Identity
        self.add_pattern(
            FraudPattern(
                id="synthetic_identity",
                name="Synthetic Identity Fraud",
                description="Fake identity created from real and fake information",
                rules=[
                    Rule(
                        "identity_verification_score",
                        Operator.LESS_THAN,
                        0.5,
                        "Low identity verification score",
                    ),
                    Rule(
                        "inconsistent_data",
                        Operator.EQUALS,
                        True,
                        "Inconsistent personal information",
                    ),
                    Rule(
                        "recent_account_creation", Operator.EQUALS, True, "Recently created account"
                    ),
                ],
                severity=Severity.HIGH,
                category="identity_fraud",
            )
        )

        logger.info(f"Loaded {len(self.patterns)} default fraud patterns")

    def add_pattern(self, pattern: FraudPattern):
        """Add a pattern to the library"""
        self.patterns[pattern.id] = pattern
        logger.info(f"Added pattern: {pattern.name}")

    def remove_pattern(self, pattern_id: str):
        """Remove a pattern from the library"""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            logger.info(f"Removed pattern: {pattern_id}")

    def get_pattern(self, pattern_id: str) -> Optional[FraudPattern]:
        """Get a specific pattern"""
        return self.patterns.get(pattern_id)

    def detect(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect fraud patterns in data.

        Args:
            data: Transaction or user data

        Returns:
            List of matched patterns with details
        """
        matches = []

        for pattern_id, pattern in self.patterns.items():
            if pattern.matches(data):
                matches.append(
                    {
                        "pattern_id": pattern_id,
                        "pattern_name": pattern.name,
                        "description": pattern.description,
                        "severity": pattern.severity.value,
                        "category": pattern.category,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        return matches

    def get_patterns_by_category(self, category: str) -> List[FraudPattern]:
        """Get all patterns in a category"""
        return [p for p in self.patterns.values() if p.category == category]

    def get_patterns_by_severity(self, severity: Severity) -> List[FraudPattern]:
        """Get all patterns with specific severity"""
        return [p for p in self.patterns.values() if p.severity == severity]

    def enable_pattern(self, pattern_id: str):
        """Enable a pattern"""
        if pattern_id in self.patterns:
            self.patterns[pattern_id].enabled = True

    def disable_pattern(self, pattern_id: str):
        """Disable a pattern"""
        if pattern_id in self.patterns:
            self.patterns[pattern_id].enabled = False

    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics"""
        total = len(self.patterns)
        enabled = sum(1 for p in self.patterns.values() if p.enabled)

        by_severity = {}
        for severity in Severity:
            by_severity[severity.value] = len(self.get_patterns_by_severity(severity))

        by_category = {}
        categories = set(p.category for p in self.patterns.values())
        for category in categories:
            by_category[category] = len(self.get_patterns_by_category(category))

        return {
            "total_patterns": total,
            "enabled_patterns": enabled,
            "disabled_patterns": total - enabled,
            "by_severity": by_severity,
            "by_category": by_category,
        }


# Global instance
_pattern_library = None


def get_pattern_library() -> PatternLibrary:
    """Get global pattern library instance"""
    global _pattern_library
    if _pattern_library is None:
        _pattern_library = PatternLibrary()
    return _pattern_library


# Example usage
if __name__ == "__main__":
    library = PatternLibrary()

    # Example transaction data
    transaction_data = {
        "transaction_count": 15,
        "time_window_seconds": 45,
        "amount": 5000,
        "amount_deviation": 2.5,
        "distance_from_usual_km": 1500,
        "time_since_last_transaction_hours": 1,
    }

    # Detect patterns
    detected = library.detect(transaction_data)

    print(f"Detected {len(detected)} fraud patterns:")
    for match in detected:
        print(f"  - {match['pattern_name']} ({match['severity']}): {match['description']}")

    # Get statistics
    stats = library.get_statistics()
    print(f"\nLibrary Statistics:")
    print(f"  Total patterns: {stats['total_patterns']}")
    print(f"  By severity: {stats['by_severity']}")
    print(f"  By category: {stats['by_category']}")
