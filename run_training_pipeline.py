#!/usr/bin/env python3
"""
FSMGuard — Complete Training Pipeline Runner
============================================
Runs the complete training pipeline:
1. Generate 20,000 synthetic FSMs
2. Train GAT model
3. Test thresholds
"""
import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print("\n" + "=" * 80)
    print(f"Running: {script_name}")
    print(f"Description: {description}")
    print("=" * 80 + "\n")
    
    result = subprocess.run([sys.executable, script_name], 
                          capture_output=False, 
                          text=True)
    
    if result.returncode != 0:
        print(f"\n❌ Error running {script_name}")
        print(f"Exit code: {result.returncode}")
        sys.exit(1)
    
    print(f"\n✅ {script_name} completed successfully\n")

def main():
    """Run complete pipeline."""
    print("=" * 80)
    print("FSMGuard — Complete Training Pipeline")
    print("=" * 80)
    print("\nThis will run three scripts in sequence:")
    print("  1. generate.py       → Generate 20,000 synthetic FSMs")
    print("  2. train.py          → Train GAT model")
    print("  3. threshold_test.py → Find optimal threshold")
    print("\nEstimated time: 30-60 minutes depending on hardware")
    print("=" * 80)
    
    input("\nPress Enter to start pipeline (or Ctrl+C to cancel)...")
    
    # Ensure we're in the correct directory
    os.chdir('/Users/sahebsandhu/sandbx/FSMGuard')
    
    # Step 1: Generate dataset
    run_script('generate.py', 'Generate synthetic FSM dataset')
    
    # Step 2: Train model
    run_script('train.py', 'Train GAT model on dataset')
    
    # Step 3: Test thresholds
    run_script('threshold_test.py', 'Find optimal detection threshold')
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  ✓ fsm_dataset.pt      - Training dataset (20,000 FSMs)")
    print("  ✓ fsm_gat_model.pth   - Final trained model")
    print("  ✓ fsm_gat_best.pth    - Best model (highest validation F1)")
    print("\nYou can now test detection:")
    print("  python3 test_vulnerable.py")
    print("  python3 validate_pipeline.py")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
