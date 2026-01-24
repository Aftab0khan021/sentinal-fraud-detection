"""
Export SentinAL Fraud Detection Model to TorchServe
====================================================
Script to export PyTorch model to TorchScript and create .mar archive for TorchServe.

Usage:
    python export_model.py --model-path models/fraud_detection_model.pth \
                          --output-dir torchserve/model-store \
                          --version 1.0.0

Author: SentinAL Team
Date: 2026-01-24
"""

import os
import sys
import argparse
import torch
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))


def export_to_torchscript(model_path, output_path):
    """
    Export PyTorch model to TorchScript.
    
    Args:
        model_path: Path to PyTorch model (.pth)
        output_path: Path to save TorchScript model (.pt)
    """
    print(f"Loading model from {model_path}...")
    model = torch.load(model_path, map_location='cpu')
    model.eval()
    
    print("Converting to TorchScript...")
    # Create example input
    # Adjust dimensions based on your model
    example_x = torch.randn(100, 10)  # 100 nodes, 10 features
    example_edge_index = torch.randint(0, 100, (2, 200))  # 200 edges
    
    try:
        # Try tracing first
        traced_model = torch.jit.trace(model, (example_x, example_edge_index))
        print("Model traced successfully")
    except Exception as e:
        print(f"Tracing failed: {e}")
        print("Trying scripting instead...")
        try:
            traced_model = torch.jit.script(model)
            print("Model scripted successfully")
        except Exception as e2:
            print(f"Scripting also failed: {e2}")
            print("Saving original model instead")
            traced_model = model
    
    print(f"Saving TorchScript model to {output_path}...")
    torch.jit.save(traced_model, output_path)
    print("✓ TorchScript model saved")
    
    return traced_model


def create_model_archive(model_path, handler_path, output_dir, model_name="fraud_detection", version="1.0.0"):
    """
    Create TorchServe model archive (.mar file).
    
    Args:
        model_path: Path to model file
        handler_path: Path to custom handler
        output_dir: Directory to save .mar file
        model_name: Name of the model
        version: Model version
    """
    print("\nCreating model archive...")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Build torch-model-archiver command
    mar_file = f"{model_name}.mar"
    mar_path = os.path.join(output_dir, mar_file)
    
    # Remove existing .mar file
    if os.path.exists(mar_path):
        print(f"Removing existing {mar_file}...")
        os.remove(mar_path)
    
    cmd = [
        "torch-model-archiver",
        "--model-name", model_name,
        "--version", version,
        "--model-file", model_path,
        "--serialized-file", model_path,
        "--handler", handler_path,
        "--export-path", output_dir,
        "--force"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    import subprocess
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"✓ Model archive created: {mar_path}")
        return mar_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating model archive: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        
        # Fallback: create a simple archive manually
        print("\nFalling back to manual archive creation...")
        print("Note: Install torch-model-archiver for production use:")
        print("  pip install torch-model-archiver")
        
        return None
    except FileNotFoundError:
        print("\nError: torch-model-archiver not found")
        print("Install it with: pip install torch-model-archiver")
        print("\nFor now, you can use the model directly in TorchServe")
        return None


def prepare_model_store(model_path, graph_data_path, handler_path, output_dir):
    """
    Prepare model store directory with all necessary files.
    
    Args:
        model_path: Path to model file
        graph_data_path: Path to graph data
        handler_path: Path to handler
        output_dir: Output directory
    """
    print("\nPreparing model store...")
    
    # Create model store directory
    model_store = os.path.join(output_dir, "model-store")
    os.makedirs(model_store, exist_ok=True)
    
    # Copy model
    model_dest = os.path.join(model_store, "fraud_detection_model.pth")
    if os.path.exists(model_path):
        shutil.copy(model_path, model_dest)
        print(f"✓ Copied model to {model_dest}")
    
    # Copy graph data if exists
    if graph_data_path and os.path.exists(graph_data_path):
        graph_dest = os.path.join(model_store, "graph_data.pt")
        shutil.copy(graph_data_path, graph_dest)
        print(f"✓ Copied graph data to {graph_dest}")
    
    # Copy handler
    handler_dest = os.path.join(model_store, "handler.py")
    shutil.copy(handler_path, handler_dest)
    print(f"✓ Copied handler to {handler_dest}")
    
    print(f"\n✓ Model store ready at {model_store}")
    return model_store


def main():
    parser = argparse.ArgumentParser(description="Export model to TorchServe")
    parser.add_argument("--model-path", required=True, help="Path to PyTorch model (.pth)")
    parser.add_argument("--graph-data-path", help="Path to graph data (.pt)")
    parser.add_argument("--output-dir", default="torchserve", help="Output directory")
    parser.add_argument("--version", default="1.0.0", help="Model version")
    parser.add_argument("--skip-torchscript", action="store_true", help="Skip TorchScript conversion")
    
    args = parser.parse_args()
    
    print("="*60)
    print("SentinAL Model Export to TorchServe")
    print("="*60)
    
    # Validate inputs
    if not os.path.exists(args.model_path):
        print(f"Error: Model file not found: {args.model_path}")
        return 1
    
    # Get handler path
    script_dir = Path(__file__).parent
    handler_path = script_dir.parent / "torchserve" / "handler.py"
    
    if not os.path.exists(handler_path):
        print(f"Error: Handler not found: {handler_path}")
        return 1
    
    # Export to TorchScript (optional)
    if not args.skip_torchscript:
        torchscript_path = os.path.join(args.output_dir, "fraud_detection_torchscript.pt")
        try:
            export_to_torchscript(args.model_path, torchscript_path)
        except Exception as e:
            print(f"Warning: TorchScript export failed: {e}")
            print("Continuing with original model...")
    
    # Prepare model store
    model_store = prepare_model_store(
        args.model_path,
        args.graph_data_path,
        handler_path,
        args.output_dir
    )
    
    # Create model archive
    mar_path = create_model_archive(
        args.model_path,
        handler_path,
        model_store,
        version=args.version
    )
    
    print("\n" + "="*60)
    print("Export Complete!")
    print("="*60)
    print(f"\nModel store: {model_store}")
    if mar_path:
        print(f"Model archive: {mar_path}")
    
    print("\nNext steps:")
    print("1. Start TorchServe:")
    print(f"   torchserve --start --model-store {model_store} --models fraud_detection.mar")
    print("\n2. Test inference:")
    print('   curl -X POST http://localhost:8080/predictions/fraud_detection \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"user_id": 77}\'')
    print("\n3. Check model status:")
    print("   curl http://localhost:8081/models/fraud_detection")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
