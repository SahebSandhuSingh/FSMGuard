"""
FSMGuard - Complete Pipeline Test (Stages 1-2-3-4)
===================================================

Tests the full FSMGuard pipeline end-to-end:
Stage 1: Verilog parsing and FSM extraction
Stage 2 & 3: Graph construction and feature generation
Stage 4: Security analysis and report generation

For demo purposes, creates a mock trained model if one doesn't exist.
"""

import sys
import os
import torch

# Add paths
sys.path.insert(0, 'parser')
sys.path.insert(0, '..')

# Import all stages
from parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import stage4_pipeline, FSM_GAT


def create_mock_model(save_path="fsm_gat_best.pth"):
    """
    Create a mock trained model for testing purposes.
    
    In production, this would be replaced with actual trained weights
    from the training pipeline.
    
    Args:
        save_path: Path to save model weights
    """
    print("\n⚠️  No trained model found. Creating mock model for demo...")
    
    # Initialize model
    model = FSM_GAT()
    
    # Initialize with random weights (in production, these would be trained)
    # For demo, we'll just save the initialized model
    
    # Save model
    torch.save(model.state_dict(), save_path)
    print(f"✓ Mock model saved to: {save_path}")
    print("   (In production, use actual trained model weights)\n")


def main():
    print("=" * 70)
    print("FSMGuard - Complete Security Analysis Pipeline")
    print("=" * 70)
    
    # Configuration
    verilog_file = "input/sample_fsm.v"
    design_name = "sample_fsm"
    model_path = "fsm_gat_best.pth"
    
    # Create mock model if needed (for demo only)
    if not os.path.exists(model_path):
        create_mock_model(model_path)
    
    # ========================================================================
    # STAGE 1: Verilog Parsing and FSM Extraction
    # ========================================================================
    print("\n" + "=" * 70)
    print("STAGE 1: Verilog FSM Extraction")
    print("=" * 70)
    
    fsm_data = stage1_pipeline(verilog_file)
    
    if not fsm_data or not fsm_data.get("states"):
        print("ERROR: Stage 1 failed to extract FSM data")
        return
    
    state_names = fsm_data["states"]
    print(f"\n✓ Stage 1 Complete: {len(state_names)} states extracted")
    
    # ========================================================================
    # STAGE 2 & 3: Graph Construction and Feature Generation
    # ========================================================================
    print("\n" + "=" * 70)
    print("STAGE 2 & 3: Graph Construction and Feature Extraction")
    print("=" * 70)
    
    data = pipeline_stage2_stage3(fsm_data)
    
    print(f"\n✓ Stage 2 & 3 Complete:")
    print(f"  Feature Matrix: {data.x.shape}")
    print(f"  Edge Index: {data.edge_index.shape}")
    print(f"  Features per state: {data.x.shape[1]}")
    
    # ========================================================================
    # STAGE 4: Security Analysis and Report Generation
    # ========================================================================
    print("\n" + "=" * 70)
    print("STAGE 4: Security Analysis & Report Generation")
    print("=" * 70)
    
    report = stage4_pipeline(
        data=data,
        state_names=state_names,
        design_name=design_name,
        model_path=model_path,
        threshold=0.40
    )
    
    # ========================================================================
    # PIPELINE COMPLETE
    # ========================================================================
    if report:
        print("\n" + "=" * 70)
        print("✅ COMPLETE PIPELINE EXECUTION SUCCESSFUL")
        print("=" * 70)
        print("\nOutput Files Generated:")
        print("  - output/stage1_output.json    (FSM data)")
        print("  - output/stage4_report.json    (Security report)")
        print("\nNext Steps:")
        print("  1. Review security report for weak states")
        print("  2. Apply recommended fixes to RTL design")
        print("  3. Re-run analysis to verify improvements")
        print("=" * 70)
    else:
        print("\n✗ Pipeline execution failed at Stage 4")


if __name__ == "__main__":
    # Change to FSMGuard directory
    if os.path.basename(os.getcwd()) != "FSMGuard":
        if os.path.exists("FSMGuard"):
            os.chdir("FSMGuard")
    
    main()
