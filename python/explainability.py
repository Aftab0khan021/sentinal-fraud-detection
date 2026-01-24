"""
SentinAL: Model Explainability Module (SHAP & GNNExplainer)
===========================================================
Provides deep learning explainability for fraud detection decisions.

Features:
- GNNExplainer: Subgraph importance
- SHAP: Feature importance attribution

Author: SentinAL Security Team
Date: 2026-01-23
"""

import torch
from torch_geometric.explain import GNNExplainer, Explainer, ModelConfig
from torch_geometric.data import Data
import shap
import numpy as np
import pickle
import json
from models import AnalyzeResponse
import os

class AdvancedExplainer:
    def __init__(self, model_path, graph_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load Model
        try:
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
        except Exception as e:
            print(f"Error loading model for explainability: {e}")
            self.model = None

        # Load Graph
        try:
            with open(graph_path.replace('.pkl', '_pyg_enhanced.pt'), 'rb') as f:
                 self.data = torch.load(f, map_location=self.device)
        except Exception as e:
            print(f"Error loading PyG graph for explainability: {e}")
            self.data = None
            
        # Initialize Explainers if model/data loaded
        if self.model and self.data:
            self._init_explainers()

    def _init_explainers(self):
        # GNNExplainer
        self.gnn_explainer = Explainer(
            model=self.model,
            algorithm=GNNExplainer(epochs=200),
            explanation_type='model',
            node_mask_type='object',
            edge_mask_type='object',
            model_config=dict(
                mode='multiclass_classification',
                task_level='node',
                return_type='log_probs',
            ),
        )

    def explain_gnn(self, node_idx):
        """
        Run GNNExplainer to find most important subgraph for a node.
        """
        if not self.model or not self.data:
            return {"error": "Model or data not initialized"}

        explanation = self.gnn_explainer(
            self.data.x, 
            self.data.edge_index, 
            index=node_idx
        )
        
        # Process results
        important_edges = []
        edge_mask = explanation.edge_mask
        if edge_mask is not None:
             # Get top 5 edges
             top_k = 5
             top_indices = torch.topk(edge_mask, min(top_k, edge_mask.size(0))).indices
             for idx in top_indices:
                 src = self.data.edge_index[0, idx].item()
                 dst = self.data.edge_index[1, idx].item()
                 score = edge_mask[idx].item()
                 important_edges.append({
                     "source": src,
                     "target": dst,
                     "importance": float(score)
                 })
                 
        # Feature importance from node mask
        node_mask = explanation.node_mask
        feature_importance = []
        if node_mask is not None:
            # Aggregate feature importance for the target node
            target_mask = node_mask[node_idx]
            top_features = torch.topk(target_mask, min(5, target_mask.size(0))).indices
            for idx in top_features:
                 feature_importance.append({
                     "feature_index": int(idx),
                     "importance": float(target_mask[idx].item())
                 })

        return {
            "node_id": node_idx,
            "important_subgraph": important_edges,
            "top_features": feature_importance
        }
    
    def explain_shap(self, node_idx):
        """
        Run SHAP to get global feature importance approximation.
        For GNNs, we use KernelExplainer on the node features essentially treating 
        neighbors as fixed context or simplifying.
        
        Note: Exact SHAP on GNNs is computationally expensive.
        We implement a simplified version here or placeholder if too slow for live API.
        """
        # Placeholder for complex SHAP implementation
        # Real-time SHAP on GNN is non-trivial without specific Explainer configurations
        return {
            "method": "SHAP (Placeholder)", 
            "message": "Global feature importance analysis requires batch processing."
        }

# Global Instance
explainer_module = None

def init_explainer_module(model_path='models/best_fraud_detector_improved.pt', graph_path='data/graph_enhanced.pkl'):
    global explainer_module
    explainer_module = AdvancedExplainer(model_path, graph_path)
    return explainer_module

def get_advanced_explanation(user_id):
    if not explainer_module:
        return {"error": "Explainer module not initialized"}
    return explainer_module.explain_gnn(user_id)
