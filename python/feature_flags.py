"""
Feature Flags System for SentinAL
==================================
Provides feature flag management for safe feature rollouts and A/B testing.

Features:
- Environment-based flags
- User-based flags
- Percentage-based rollouts
- Redis-backed flag storage
- Real-time flag updates

Author: SentinAL Team
Date: 2026-01-24
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
from cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class FlagType(Enum):
    """Feature flag types"""

    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"


class FeatureFlags:
    """
    Feature flags manager with Redis backend.
    """

    def __init__(self):
        self.cache = get_cache_manager()
        self.prefix = "feature_flag:"
        self._load_default_flags()

    def _load_default_flags(self):
        """Load default feature flags from environment or config."""
        self.default_flags = {
            # Real-time streaming
            "realtime_streaming": {
                "enabled": os.getenv("FF_REALTIME_STREAMING", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Enable real-time fraud detection streaming with Kafka",
            },
            # Model serving
            "torchserve_inference": {
                "enabled": os.getenv("FF_TORCHSERVE", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Use TorchServe for model inference instead of in-process",
            },
            # A/B testing
            "model_ab_testing": {
                "enabled": os.getenv("FF_AB_TESTING", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Enable A/B testing between model versions",
            },
            # Explainability
            "advanced_explainability": {
                "enabled": os.getenv("FF_ADVANCED_EXPLAIN", "true").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Enable advanced explainability with SHAP and attention",
            },
            # GraphQL
            "graphql_api": {
                "enabled": os.getenv("FF_GRAPHQL", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Enable GraphQL API alongside REST",
            },
            # GPU inference
            "gpu_inference": {
                "enabled": os.getenv("FF_GPU_INFERENCE", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Use GPU for model inference",
            },
            # Model quantization
            "quantized_models": {
                "enabled": os.getenv("FF_QUANTIZED_MODELS", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Use quantized models for faster inference",
            },
            # Fraud pattern library
            "pattern_library": {
                "enabled": os.getenv("FF_PATTERN_LIBRARY", "false").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Enable fraud pattern library and rule engine",
            },
            # Enhanced logging
            "enhanced_logging": {
                "enabled": os.getenv("FF_ENHANCED_LOGGING", "true").lower() == "true",
                "type": FlagType.BOOLEAN,
                "description": "Enable enhanced structured logging with ELK",
            },
            # Rate limiting
            "rate_limit_per_user": {
                "enabled": True,
                "value": int(os.getenv("FF_RATE_LIMIT", "100")),
                "type": FlagType.NUMBER,
                "description": "Rate limit per user (requests per minute)",
            },
            # Model version
            "model_version": {
                "enabled": True,
                "value": os.getenv("FF_MODEL_VERSION", "1.0.0"),
                "type": FlagType.STRING,
                "description": "Active model version",
            },
            # Rollout percentage
            "new_ui_rollout": {
                "enabled": True,
                "value": int(os.getenv("FF_NEW_UI_ROLLOUT", "0")),
                "type": FlagType.NUMBER,
                "description": "Percentage of users to show new UI (0-100)",
            },
        }

    def is_enabled(
        self, flag_name: str, user_id: Optional[str] = None, default: bool = False
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag
            user_id: Optional user ID for user-specific flags
            default: Default value if flag not found

        Returns:
            True if flag is enabled, False otherwise
        """
        try:
            # Check Redis cache first
            cache_key = f"{self.prefix}{flag_name}"
            cached_value = self.cache.get(cache_key)

            if cached_value is not None:
                flag_data = json.loads(cached_value)
            else:
                # Fall back to default flags
                flag_data = self.default_flags.get(flag_name)
                if flag_data is None:
                    logger.warning(
                        f"Feature flag '{flag_name}' not found, using default: {default}"
                    )
                    return default

            # Check if flag is enabled
            if not flag_data.get("enabled", False):
                return False

            # Check percentage-based rollout
            if "rollout_percentage" in flag_data:
                percentage = flag_data["rollout_percentage"]
                if user_id:
                    # Consistent hashing for user-based rollout
                    user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                    user_percentage = user_hash % 100
                    return user_percentage < percentage
                else:
                    # Random rollout without user ID
                    import random

                    return random.randint(0, 99) < percentage

            # Check user-specific overrides
            if user_id and "user_overrides" in flag_data:
                if user_id in flag_data["user_overrides"]:
                    return flag_data["user_overrides"][user_id]

            return True

        except Exception as e:
            logger.error(f"Error checking feature flag '{flag_name}': {e}")
            return default

    def get_value(self, flag_name: str, user_id: Optional[str] = None, default: Any = None) -> Any:
        """
        Get feature flag value (for non-boolean flags).

        Args:
            flag_name: Name of the feature flag
            user_id: Optional user ID for user-specific values
            default: Default value if flag not found

        Returns:
            Flag value or default
        """
        try:
            cache_key = f"{self.prefix}{flag_name}"
            cached_value = self.cache.get(cache_key)

            if cached_value is not None:
                flag_data = json.loads(cached_value)
            else:
                flag_data = self.default_flags.get(flag_name)
                if flag_data is None:
                    return default

            if not flag_data.get("enabled", False):
                return default

            # Check user-specific overrides
            if user_id and "user_overrides" in flag_data:
                if user_id in flag_data["user_overrides"]:
                    return flag_data["user_overrides"][user_id]

            return flag_data.get("value", default)

        except Exception as e:
            logger.error(f"Error getting feature flag value '{flag_name}': {e}")
            return default

    def set_flag(
        self,
        flag_name: str,
        enabled: bool,
        value: Any = None,
        ttl: int = 3600,
        rollout_percentage: Optional[int] = None,
    ):
        """
        Set a feature flag.

        Args:
            flag_name: Name of the feature flag
            enabled: Whether flag is enabled
            value: Optional value for non-boolean flags
            ttl: Time to live in seconds (default: 1 hour)
            rollout_percentage: Optional percentage for gradual rollout (0-100)
        """
        try:
            flag_data = {
                "enabled": enabled,
                "value": value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            if rollout_percentage is not None:
                flag_data["rollout_percentage"] = max(0, min(100, rollout_percentage))

            cache_key = f"{self.prefix}{flag_name}"
            self.cache.set(cache_key, json.dumps(flag_data), ttl=ttl)

            logger.info(f"Feature flag '{flag_name}' set to {enabled} (value: {value})")

        except Exception as e:
            logger.error(f"Error setting feature flag '{flag_name}': {e}")

    def set_user_override(self, flag_name: str, user_id: str, value: Any):
        """
        Set user-specific override for a feature flag.

        Args:
            flag_name: Name of the feature flag
            user_id: User ID
            value: Override value
        """
        try:
            cache_key = f"{self.prefix}{flag_name}"
            cached_value = self.cache.get(cache_key)

            if cached_value:
                flag_data = json.loads(cached_value)
            else:
                flag_data = self.default_flags.get(flag_name, {})

            if "user_overrides" not in flag_data:
                flag_data["user_overrides"] = {}

            flag_data["user_overrides"][user_id] = value
            self.cache.set(cache_key, json.dumps(flag_data), ttl=3600)

            logger.info(f"User override set for '{flag_name}': user={user_id}, value={value}")

        except Exception as e:
            logger.error(f"Error setting user override: {e}")

    def get_all_flags(self) -> Dict[str, Any]:
        """
        Get all feature flags.

        Returns:
            Dictionary of all flags
        """
        return {
            name: {"enabled": self.is_enabled(name), "value": self.get_value(name), **flag_data}
            for name, flag_data in self.default_flags.items()
        }

    def delete_flag(self, flag_name: str):
        """
        Delete a feature flag from cache.

        Args:
            flag_name: Name of the feature flag
        """
        try:
            cache_key = f"{self.prefix}{flag_name}"
            self.cache.delete(cache_key)
            logger.info(f"Feature flag '{flag_name}' deleted from cache")
        except Exception as e:
            logger.error(f"Error deleting feature flag '{flag_name}': {e}")


# Global instance
_feature_flags = None


def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_feature_enabled(
    flag_name: str, user_id: Optional[str] = None, default: bool = False
) -> bool:
    """
    Convenience function to check if a feature is enabled.

    Args:
        flag_name: Name of the feature flag
        user_id: Optional user ID
        default: Default value if flag not found

    Returns:
        True if feature is enabled
    """
    return get_feature_flags().is_enabled(flag_name, user_id, default)


def get_feature_value(flag_name: str, user_id: Optional[str] = None, default: Any = None) -> Any:
    """
    Convenience function to get feature flag value.

    Args:
        flag_name: Name of the feature flag
        user_id: Optional user ID
        default: Default value if flag not found

    Returns:
        Feature flag value
    """
    return get_feature_flags().get_value(flag_name, user_id, default)
