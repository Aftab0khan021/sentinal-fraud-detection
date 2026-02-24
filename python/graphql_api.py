"""
GraphQL API for SentinAL Fraud Detection
=========================================
Provides a flexible GraphQL API alongside the REST API.

Features:
- Flexible queries
- Batch requests
- Real-time subscriptions
- Type-safe schema
- Automatic documentation

Author: SentinAL Team
Date: 2026-01-24
"""

import strawberry
from typing import List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@strawberry.type
class FraudAnalysis:
    """Fraud analysis result"""

    user_id: int
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    reason: Optional[str]
    explanation: str
    timestamp: str

    @strawberry.field
    def confidence(self) -> float:
        """Calculate confidence score (0-1)"""
        return abs(self.fraud_probability - 0.5) * 2


@strawberry.type
class GraphNode:
    """Transaction graph node"""

    id: str
    is_fraud: bool
    risk_score: float
    fraud_probability: float

    @strawberry.field
    def risk_level(self) -> str:
        """Get risk level based on probability"""
        if self.fraud_probability >= 0.8:
            return "critical"
        elif self.fraud_probability >= 0.6:
            return "high"
        elif self.fraud_probability >= 0.4:
            return "medium"
        elif self.fraud_probability >= 0.2:
            return "low"
        else:
            return "minimal"


@strawberry.type
class GraphEdge:
    """Transaction graph edge"""

    source: str
    target: str
    amount: float
    is_laundering: bool


@strawberry.type
class TransactionGraph:
    """Full transaction graph"""

    nodes: List[GraphNode]
    edges: List[GraphEdge]

    @strawberry.field
    def total_nodes(self) -> int:
        return len(self.nodes)

    @strawberry.field
    def total_edges(self) -> int:
        return len(self.edges)

    @strawberry.field
    def fraud_rate(self) -> float:
        """Calculate percentage of fraudulent nodes"""
        if not self.nodes:
            return 0.0
        fraud_count = sum(1 for node in self.nodes if node.is_fraud)
        return (fraud_count / len(self.nodes)) * 100


@strawberry.type
class FeatureFlag:
    """Feature flag"""

    name: str
    enabled: bool
    value: Optional[str]
    description: str


@strawberry.type
class SystemHealth:
    """System health status"""

    status: str
    timestamp: str
    version: str
    instance_id: str
    cache_status: str
    uptime_seconds: float


@strawberry.type
class Query:
    """GraphQL queries"""

    @strawberry.field
    def analyze_user(self, user_id: int) -> FraudAnalysis:
        """
        Analyze a single user for fraud.

        Example:
            query {
                analyzeUser(userId: 77) {
                    userId
                    fraudProbability
                    isFraud
                    riskLevel
                    confidence
                    explanation
                }
            }
        """
        # Import here to avoid circular imports
        from agent_explainer import FraudExplainerAgent
        from cache_manager import get_cache_manager

        # Check cache
        cache = get_cache_manager()
        cache_key = f"fraud_analysis:{user_id}"
        cached = cache.get(cache_key)

        if cached:
            import json

            data = json.loads(cached)
            return FraudAnalysis(**data)

        # Analyze user
        # TODO: Implement actual analysis
        # For now, return mock data
        result = {
            "user_id": user_id,
            "fraud_probability": 0.75,
            "is_fraud": True,
            "risk_level": "high",
            "reason": "Suspicious transaction pattern",
            "explanation": "User exhibits high-risk behavior...",
            "timestamp": datetime.now(timezone.utc).isoformat(),  # was deprecated utcnow()
        }

        # Cache result
        import json

        cache.set(cache_key, json.dumps(result), ttl=300)

        return FraudAnalysis(**result)

    @strawberry.field
    def analyze_users(self, user_ids: List[int]) -> List[FraudAnalysis]:
        """
        Analyze multiple users in batch.

        Example:
            query {
                analyzeUsers(userIds: [77, 78, 79]) {
                    userId
                    isFraud
                    riskLevel
                }
            }
        """
        return [self.analyze_user(user_id) for user_id in user_ids]

    @strawberry.field
    def transaction_graph(self) -> TransactionGraph:
        """
        Get the full transaction graph.

        Example:
            query {
                transactionGraph {
                    totalNodes
                    totalEdges
                    fraudRate
                    nodes {
                        id
                        riskLevel
                    }
                }
            }
        """
        # TODO: Load actual graph data
        # For now, return mock data
        nodes = [
            GraphNode(id=str(i), is_fraud=i % 3 == 0, risk_score=0.5, fraud_probability=0.6)
            for i in range(10)
        ]
        edges = [
            GraphEdge(source=str(i), target=str(i + 1), amount=100.0, is_laundering=False)
            for i in range(9)
        ]

        return TransactionGraph(nodes=nodes, edges=edges)

    @strawberry.field
    def feature_flags(self) -> List[FeatureFlag]:
        """
        Get all feature flags.

        Example:
            query {
                featureFlags {
                    name
                    enabled
                    description
                }
            }
        """
        from feature_flags import get_feature_flags

        flags_data = get_feature_flags().get_all_flags()

        return [
            FeatureFlag(
                name=name,
                enabled=data.get("enabled", False),
                value=str(data.get("value", "")),
                description=data.get("description", ""),
            )
            for name, data in flags_data.items()
        ]

    @strawberry.field
    def system_health(self) -> SystemHealth:
        """
        Get system health status.

        Example:
            query {
                systemHealth {
                    status
                    version
                    instanceId
                    cacheStatus
                }
            }
        """
        import os
        import time
        from cache_manager import get_cache_manager

        # Import VERSION constant from api configuration
        try:
            from api import VERSION as _version
        except ImportError:
            _version = os.getenv("API_VERSION", "2.0.0")

        cache = get_cache_manager()
        cache_health = cache.health_check()

        return SystemHealth(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),  # was deprecated utcnow()
            version=_version,  # was hardcoded "2.0.0"
            instance_id=os.getenv("INSTANCE_ID", "unknown"),
            cache_status=cache_health.get("status", "unknown"),
            uptime_seconds=time.time(),  # TODO: Track actual uptime
        )


@strawberry.type
class Mutation:
    """GraphQL mutations"""

    @strawberry.mutation
    def set_feature_flag(
        self, name: str, enabled: bool, rollout_percentage: Optional[int] = None
    ) -> FeatureFlag:
        """
        Set a feature flag.

        Example:
            mutation {
                setFeatureFlag(name: "realtime_streaming", enabled: true, rolloutPercentage: 50) {
                    name
                    enabled
                }
            }
        """
        from feature_flags import get_feature_flags

        flags = get_feature_flags()
        flags.set_flag(name, enabled, rollout_percentage=rollout_percentage)

        all_flags = flags.get_all_flags()
        flag_data = all_flags.get(name, {})

        return FeatureFlag(
            name=name,
            enabled=enabled,
            value=str(flag_data.get("value", "")),
            description=flag_data.get("description", ""),
        )


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


def get_graphql_app():
    """
    Get GraphQL app for FastAPI integration.

    Usage in api.py:
        from graphql_api import get_graphql_app
        from feature_flags import is_feature_enabled

        if is_feature_enabled("graphql_api"):
            from strawberry.fastapi import GraphQLRouter
            graphql_app = GraphQLRouter(schema)
            app.include_router(graphql_app, prefix="/graphql")
    """
    from strawberry.fastapi import GraphQLRouter

    return GraphQLRouter(schema)
