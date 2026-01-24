"""
TorchServe Custom Handler for SentinAL Fraud Detection Model
==============================================================
Custom handler for serving the GNN fraud detection model via TorchServe.

Features:
- Graph data preprocessing
- Batch inference support
- Model versioning
- Metrics collection
- Error handling

Author: SentinAL Team
Date: 2026-01-24
"""

import os
import json
import logging
import torch
import torch.nn.functional as F
from torch_geometric.data import Data, Batch
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class FraudDetectionHandler(BaseHandler):
    """
    Custom TorchServe handler for fraud detection GNN model.
    """
    
    def __init__(self):
        super(FraudDetectionHandler, self).__init__()
        self.initialized = False
        self.device = None
        self.model = None
        self.graph_data = None
        
    def initialize(self, context):
        """
        Initialize model and load graph data.
        
        Args:
            context: TorchServe context with model artifacts
        """
        try:
            # Get model properties
            properties = context.system_properties
            self.device = torch.device(
                "cuda:" + str(properties.get("gpu_id")) 
                if torch.cuda.is_available() 
                else "cpu"
            )
            
            # Load model
            model_dir = properties.get("model_dir")
            model_path = os.path.join(model_dir, "fraud_detection_model.pth")
            
            logger.info(f"Loading model from {model_path}")
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            
            # Load graph data
            graph_data_path = os.path.join(model_dir, "graph_data.pt")
            if os.path.exists(graph_data_path):
                logger.info(f"Loading graph data from {graph_data_path}")
                self.graph_data = torch.load(graph_data_path, map_location=self.device)
            else:
                logger.warning("Graph data not found, will use request data")
            
            self.initialized = True
            logger.info("Model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    def preprocess(self, requests):
        """
        Preprocess incoming requests.
        
        Args:
            requests: List of request objects
            
        Returns:
            Preprocessed data ready for inference
        """
        try:
            batch_data = []
            
            for request in requests:
                # Parse request body
                body = request.get("body")
                if isinstance(body, (bytes, bytearray)):
                    body = body.decode('utf-8')
                
                data = json.loads(body)
                user_id = data.get("user_id")
                
                if user_id is None:
                    raise ValueError("user_id is required")
                
                # Create graph data for this user
                # In production, you might fetch this from a database
                if self.graph_data is not None:
                    # Use pre-loaded graph data
                    graph = self.graph_data
                else:
                    # Create minimal graph data from request
                    # This is a simplified version - in production, 
                    # you'd fetch the actual graph structure
                    num_nodes = data.get("num_nodes", 100)
                    num_features = data.get("num_features", 10)
                    
                    x = torch.randn(num_nodes, num_features)
                    edge_index = torch.randint(0, num_nodes, (2, num_nodes * 2))
                    
                    graph = Data(x=x, edge_index=edge_index)
                
                # Add user_id as metadata
                graph.user_id = user_id
                batch_data.append(graph)
            
            # Batch graphs together
            if len(batch_data) > 1:
                batched_graph = Batch.from_data_list(batch_data)
            else:
                batched_graph = batch_data[0]
            
            return batched_graph.to(self.device)
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise
    
    def inference(self, data):
        """
        Run model inference.
        
        Args:
            data: Preprocessed graph data
            
        Returns:
            Model predictions
        """
        try:
            with torch.no_grad():
                # Run model
                output = self.model(data.x, data.edge_index)
                
                # Apply softmax to get probabilities
                probabilities = F.softmax(output, dim=1)
                
                # Get fraud probability (class 1)
                fraud_probs = probabilities[:, 1]
                
                # Get predictions (threshold at 0.5)
                predictions = (fraud_probs > 0.5).long()
            
            return {
                'fraud_probabilities': fraud_probs.cpu().numpy(),
                'predictions': predictions.cpu().numpy(),
                'raw_output': output.cpu().numpy()
            }
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise
    
    def postprocess(self, inference_output):
        """
        Postprocess inference output.
        
        Args:
            inference_output: Raw model output
            
        Returns:
            List of formatted responses
        """
        try:
            fraud_probs = inference_output['fraud_probabilities']
            predictions = inference_output['predictions']
            
            responses = []
            for i, (prob, pred) in enumerate(zip(fraud_probs, predictions)):
                response = {
                    'fraud_probability': float(prob),
                    'is_fraud': bool(pred),
                    'confidence': float(abs(prob - 0.5) * 2),  # 0-1 scale
                    'risk_level': self._get_risk_level(float(prob))
                }
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Postprocessing failed: {e}")
            raise
    
    def _get_risk_level(self, probability):
        """
        Convert probability to risk level.
        
        Args:
            probability: Fraud probability (0-1)
            
        Returns:
            Risk level string
        """
        if probability >= 0.8:
            return "critical"
        elif probability >= 0.6:
            return "high"
        elif probability >= 0.4:
            return "medium"
        elif probability >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def handle(self, data, context):
        """
        Main entry point for TorchServe.
        
        Args:
            data: Input data
            context: TorchServe context
            
        Returns:
            Prediction results
        """
        try:
            # Preprocess
            preprocessed_data = self.preprocess(data)
            
            # Inference
            inference_output = self.inference(preprocessed_data)
            
            # Postprocess
            response = self.postprocess(inference_output)
            
            return response
            
        except Exception as e:
            logger.error(f"Handler failed: {e}")
            return [{"error": str(e)}]


# Entry point for TorchServe
_service = FraudDetectionHandler()


def handle(data, context):
    """
    TorchServe entry point.
    """
    if not _service.initialized:
        _service.initialize(context)
    
    return _service.handle(data, context)
