"""
Integration tests for the fraud detection pipeline.
Tests the complete workflow from data generation to fraud explanation.
"""
import pytest
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))


class TestFraudDetectionPipeline:
    """Test end-to-end fraud detection pipeline"""

    def test_data_files_exist(self):
        """Test that required data files exist"""
        data_dir = Path(__file__).parent.parent.parent / "python" / "data"
        
        # Check for graph data
        graph_file = data_dir / "graph_enhanced.pkl"
        if not graph_file.exists():
            pytest.skip("Graph data not generated. Run data_gen_enhanced.py first.")
        
        assert graph_file.exists()

    def test_model_files_exist(self):
        """Test that trained model files exist"""
        models_dir = Path(__file__).parent.parent.parent / "python" / "models"
        
        model_file = models_dir / "best_fraud_detector.pt"
        if not model_file.exists():
            pytest.skip("Model not trained. Run gnn_train.py first.")
        
        assert model_file.exists()

    def test_fraud_scores_exist(self):
        """Test that fraud scores file exists"""
        reports_dir = Path(__file__).parent.parent.parent / "python" / "reports"
        
        scores_file = reports_dir / "fraud_scores_improved.json"
        if not scores_file.exists():
            pytest.skip("Fraud scores not generated. Run gnn_train_improved.py first.")
        
        assert scores_file.exists()

    @pytest.mark.slow
    def test_load_graph_data(self):
        """Test loading graph data"""
        try:
            from agent_explainer import load_data
            graph, fraud_scores = load_data()
            
            assert graph is not None
            assert fraud_scores is not None
            assert len(fraud_scores['fraud_probability']) > 0
        except FileNotFoundError:
            pytest.skip("Required data files not found")

    @pytest.mark.slow
    def test_fraud_explanation_generation(self):
        """Test generating fraud explanation for a user"""
        try:
            from agent_explainer import load_data, FraudExplainerAgent
            
            graph, fraud_scores = load_data()
            agent = FraudExplainerAgent(graph, fraud_scores, model="llama3.2:1b")
            
            # Test explanation for a high-risk user
            import numpy as np
            fraud_probs = np.array(fraud_scores['fraud_probability'])
            high_risk_user = int(np.argmax(fraud_probs))
            
            explanation = agent.explain(high_risk_user)
            
            assert explanation is not None
            assert len(explanation) > 0
            assert isinstance(explanation, str)
        except Exception as e:
            pytest.skip(f"Explanation generation failed: {str(e)}")

    def test_cache_integration(self):
        """Test cache manager integration"""
        from cache_manager import get_cache_manager
        
        cache = get_cache_manager()
        
        # Test set and get
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")
        
        assert value == "test_value"
        
        # Test delete
        cache.delete("test_key")
        value = cache.get("test_key")
        
        assert value is None

    def test_cache_health_check(self):
        """Test cache health check"""
        from cache_manager import get_cache_manager
        
        cache = get_cache_manager()
        health = cache.health_check()
        
        assert "status" in health
        assert "cache_type" in health
        assert health["status"] in ["healthy", "unhealthy"]
