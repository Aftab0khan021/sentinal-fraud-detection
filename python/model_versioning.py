"""
MLflow Model Versioning and Registry for SentinAL
==================================================
Provides model versioning, experiment tracking, and A/B testing integration.

Features:
- Model versioning and registry
- Experiment tracking
- Model comparison
- A/B testing integration
- Model deployment management

Author: SentinAL Team
Date: 2026-01-24
"""

import os
import mlflow
import mlflow.pytorch
import torch
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from feature_flags import is_feature_enabled, get_feature_value

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    MLflow-based model registry for version management.
    """
    
    def __init__(self, tracking_uri: str = None):
        """
        Initialize model registry.
        
        Args:
            tracking_uri: MLflow tracking server URI (default: file-based)
        """
        if tracking_uri is None:
            tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
        
        mlflow.set_tracking_uri(tracking_uri)
        self.model_name = "fraud_detection"
        
        logger.info(f"MLflow tracking URI: {tracking_uri}")
    
    def log_model(
        self,
        model: torch.nn.Module,
        version: str,
        metrics: Dict[str, float],
        params: Dict[str, Any],
        artifacts: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Log a model to MLflow registry.
        
        Args:
            model: PyTorch model
            version: Model version string
            metrics: Performance metrics (accuracy, precision, recall, etc.)
            params: Model parameters (architecture, hyperparameters, etc.)
            artifacts: Additional artifacts to log (graphs, plots, etc.)
            
        Returns:
            Run ID
        """
        with mlflow.start_run(run_name=f"{self.model_name}_v{version}") as run:
            # Log parameters
            mlflow.log_params(params)
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log model
            mlflow.pytorch.log_model(
                model,
                "model",
                registered_model_name=self.model_name
            )
            
            # Log additional artifacts
            if artifacts:
                for name, path in artifacts.items():
                    mlflow.log_artifact(path, artifact_path=name)
            
            # Log metadata
            mlflow.set_tag("version", version)
            mlflow.set_tag("timestamp", datetime.utcnow().isoformat())
            mlflow.set_tag("framework", "pytorch")
            mlflow.set_tag("model_type", "gnn")
            
            run_id = run.info.run_id
            logger.info(f"Model v{version} logged with run_id: {run_id}")
            
            return run_id
    
    def load_model(self, version: Optional[str] = None, stage: Optional[str] = None) -> torch.nn.Module:
        """
        Load a model from registry.
        
        Args:
            version: Specific version number (e.g., "1", "2")
            stage: Model stage ("Production", "Staging", "Archived")
            
        Returns:
            Loaded PyTorch model
        """
        if version:
            model_uri = f"models:/{self.model_name}/{version}"
        elif stage:
            model_uri = f"models:/{self.model_name}/{stage}"
        else:
            model_uri = f"models:/{self.model_name}/Production"
        
        logger.info(f"Loading model from: {model_uri}")
        model = mlflow.pytorch.load_model(model_uri)
        
        return model
    
    def promote_model(self, version: str, stage: str = "Production"):
        """
        Promote a model version to a specific stage.
        
        Args:
            version: Model version to promote
            stage: Target stage ("Production", "Staging", "Archived")
        """
        client = mlflow.tracking.MlflowClient()
        
        # Transition model version to new stage
        client.transition_model_version_stage(
            name=self.model_name,
            version=version,
            stage=stage
        )
        
        logger.info(f"Model v{version} promoted to {stage}")
    
    def compare_models(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two model versions.
        
        Args:
            version1: First model version
            version2: Second model version
            
        Returns:
            Comparison results
        """
        client = mlflow.tracking.MlflowClient()
        
        # Get model version details
        mv1 = client.get_model_version(self.model_name, version1)
        mv2 = client.get_model_version(self.model_name, version2)
        
        # Get runs
        run1 = client.get_run(mv1.run_id)
        run2 = client.get_run(mv2.run_id)
        
        comparison = {
            "version1": {
                "version": version1,
                "metrics": run1.data.metrics,
                "params": run1.data.params,
                "stage": mv1.current_stage
            },
            "version2": {
                "version": version2,
                "metrics": run2.data.metrics,
                "params": run2.data.params,
                "stage": mv2.current_stage
            }
        }
        
        return comparison
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all model versions.
        
        Returns:
            List of model version details
        """
        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='{self.model_name}'")
        
        return [
            {
                "version": v.version,
                "stage": v.current_stage,
                "run_id": v.run_id,
                "created_at": v.creation_timestamp
            }
            for v in versions
        ]


class ABTestingManager:
    """
    A/B testing manager with MLflow integration.
    """
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self._model_cache = {}
    
    def get_model_for_user(self, user_id: str) -> torch.nn.Module:
        """
        Get model for user based on A/B testing configuration.
        
        Args:
            user_id: User ID for consistent assignment
            
        Returns:
            Model instance
        """
        # Check if A/B testing is enabled
        if not is_feature_enabled("model_ab_testing", user_id):
            # Return production model
            return self._get_cached_model("production")
        
        # Get model version from feature flag
        model_version = get_feature_value("model_version", user_id, default="1")
        
        # Load model
        return self._get_cached_model(model_version)
    
    def _get_cached_model(self, version: str) -> torch.nn.Module:
        """
        Get model from cache or load from registry.
        
        Args:
            version: Model version or stage
            
        Returns:
            Cached model instance
        """
        if version not in self._model_cache:
            if version == "production":
                self._model_cache[version] = self.registry.load_model(stage="Production")
            else:
                self._model_cache[version] = self.registry.load_model(version=version)
        
        return self._model_cache[version]
    
    def track_prediction(self, user_id: str, model_version: str, prediction: Dict[str, Any]):
        """
        Track prediction for A/B testing analysis.
        
        Args:
            user_id: User ID
            model_version: Model version used
            prediction: Prediction result
        """
        # Log to MLflow
        with mlflow.start_run(run_name=f"prediction_{user_id}"):
            mlflow.log_param("user_id", user_id)
            mlflow.log_param("model_version", model_version)
            mlflow.log_metric("fraud_probability", prediction.get("fraud_probability", 0))
            mlflow.log_metric("is_fraud", int(prediction.get("is_fraud", False)))
            mlflow.set_tag("timestamp", datetime.utcnow().isoformat())


# Global instances
_registry = None
_ab_manager = None


def get_model_registry() -> ModelRegistry:
    """Get global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def get_ab_testing_manager() -> ABTestingManager:
    """Get global A/B testing manager instance."""
    global _ab_manager
    if _ab_manager is None:
        _ab_manager = ABTestingManager(get_model_registry())
    return _ab_manager


# Example usage
if __name__ == "__main__":
    # Initialize registry
    registry = ModelRegistry()
    
    # Log a model
    model = torch.nn.Linear(10, 2)  # Example model
    run_id = registry.log_model(
        model=model,
        version="1.0.0",
        metrics={
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.94,
            "f1_score": 0.935
        },
        params={
            "architecture": "R-GCN",
            "num_layers": 3,
            "hidden_dim": 128,
            "learning_rate": 0.001
        }
    )
    
    print(f"Model logged with run_id: {run_id}")
    
    # List models
    models = registry.list_models()
    print(f"Available models: {models}")
    
    # Load model
    loaded_model = registry.load_model(version="1")
    print(f"Model loaded: {type(loaded_model)}")
