#!/usr/bin/env python3
"""
FSMGuard - Enhanced Pipeline Wrapper with SystemVerilog Support
================================================================

This script wraps the FSMGuard pipeline to automatically detect and handle
both Verilog and SystemVerilog FSM designs.

Usage:
    python run_fsmguard.py <input.v|input.sv> [options]

Options:
    --output-dir DIR    Output directory for results (default: ./output)
    --force-sv          Force SystemVerilog parsing
    --force-verilog     Force standard Verilog parsing
    --verbose           Enable verbose output

Author: FSMGuard Team
Date: 2026-03-08
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add parser directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'parser'))

from parser.parse_systemverilog import (
    parse_fsm_automatic,
    parse_systemverilog_fsm,
    is_systemverilog_file
)
from parser.parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import stage4_pipeline


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='FSMGuard - RTL Security Analyzer with SystemVerilog Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Automatic detection
  python run_fsmguard.py input/fsm.v
  python run_fsmguard.py input/fsm.sv
  
  # Force SystemVerilog parsing
  python run_fsmguard.py input/fsm.sv --force-sv
  
  # Specify output directory
  python run_fsmguard.py input/fsm.v --output-dir results/
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Input Verilog or SystemVerilog file'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory for results (default: ./output)'
    )
    
    parser.add_argument(
        '--force-sv',
        action='store_true',
        help='Force SystemVerilog parsing'
    )
    
    parser.add_argument(
        '--force-verilog',
        action='store_true',
        help='Force standard Verilog parsing'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def run_stage1_parsing(input_file: str, force_mode: str = 'auto', verbose: bool = False):
    """
    Run Stage 1: Parse Verilog/SystemVerilog FSM.
    
    Args:
        input_file: Path to input file
        force_mode: 'auto', 'systemverilog', or 'verilog'
        verbose: Enable verbose output
    
    Returns:
        Dictionary with parsed FSM data
    """
    if verbose:
        print("\n" + "="*70)
        print("STAGE 1: FSM PARSING")
        print("="*70)
        print(f"Input file: {input_file}")
    
    # Determine parsing mode
    if force_mode == 'systemverilog':
        if verbose:
            print("Mode: Forced SystemVerilog")
        result = parse_systemverilog_fsm(input_file)
    elif force_mode == 'verilog':
        if verbose:
            print("Mode: Forced Verilog")
        result = stage1_pipeline(input_file, output_path=None)
    else:
        if verbose:
            print("Mode: Automatic detection")
        result = parse_fsm_automatic(input_file)

    # Normalise result shape — parse_verilog_v2.stage1_pipeline() returns only
    # {"states", "transitions", "reset_state"}, while the SystemVerilog parser
    # additionally provides "module", "state_count", and "transition_count".
    # Downstream code (and print_summary) assumes all keys exist.
    if 'module' not in result:
        # Try to derive a module name from the input filename
        result['module'] = Path(input_file).stem
    result.setdefault('state_count', len(result.get('states', [])))
    result.setdefault('transition_count', len(result.get('transitions', [])))

    if verbose:
        print(f"\nModule: {result['module']}")
        print(f"States found: {result['state_count']}")
        print(f"Transitions found: {result['transition_count']}")
        print(f"Reset state: {result.get('reset_state', 'Unknown')}")
        
        if 'systemverilog_features' in result:
            sv = result['systemverilog_features']
            print(f"\n SystemVerilog Features:")
            print(f"  ├─ Enum states: {sv['total_enum_states']}")
            print(f"  ├─ Typedef states: {sv['total_typedef_states']}")
            print(f"  └─ Parameter states: {sv['total_parameter_states']}")
        
        print(f"\nStates: {', '.join(result['states'][:10])}", end='')
        if len(result['states']) > 10:
            print(f" ... ({len(result['states']) - 10} more)")
        else:
            print()
    
    return result


def run_stages2_3_4(stage1_output: dict, verbose: bool = False):
    """
    Run Stages 2-4: Graph construction, feature extraction, and GNN detection.
    
    Args:
        stage1_output: Output from stage 1
        verbose: Enable verbose output
    
    Returns:
        Dictionary with detection results
    """
    if verbose:
        print("\n" + "="*70)
        print("STAGES 2-4: GRAPH CONSTRUCTION, FEATURES & GNN DETECTION")
        print("="*70)
    
    # Run pipeline stages 2-3 (returns PyG Data object)
    data = pipeline_stage2_stage3(stage1_output)
    
    # Run stage 4 (GNN detection and report generation)
    state_names = stage1_output.get('states', [])
    module_name = stage1_output.get('module', 'FSM_Design')
    
    # Call stage4 with suppress output unless verbose
    import sys
    import io
    
    if not verbose:
        # Suppress stage4 output when not in verbose mode
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
    
    try:
        result = stage4_pipeline(
            data,
            state_names,
            design_name=module_name,
            model_path="fsm_gat_best.pth",
            output_path="output/stage4_report.json",
            threshold=0.40
        )
    finally:
        if not verbose:
            sys.stdout = old_stdout
    
    if verbose and 'weak_states' in result:
        print(f"\n⚠️  Weak states detected: {len(result['weak_states'])}")
        for state in result['weak_states'][:5]:
            risk = state.get('risk_score', 0)
            state_name = state.get('state', 'Unknown')
            print(f"  ├─ {state_name}: {risk:.2%} risk")
        if len(result['weak_states']) > 5:
            print(f"  └─ ... ({len(result['weak_states']) - 5} more)")
    
    return result


def save_results(stage1_out: dict, stage4_out: dict, output_dir: str, verbose: bool = False):
    """
    Save all results to output directory.
    
    Args:
        stage1_out: Stage 1 parsing output
        stage4_out: Stage 4 detection output
        output_dir: Output directory path
        verbose: Enable verbose output
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save stage 1 output
    stage1_file = os.path.join(output_dir, 'stage1_parsing.json')
    with open(stage1_file, 'w') as f:
        json.dump(stage1_out, f, indent=2)
    
    # Save stage 4 output
    stage4_file = os.path.join(output_dir, 'stage4_detection.json')
    with open(stage4_file, 'w') as f:
        json.dump(stage4_out, f, indent=2)
    
    if verbose:
        print("\n" + "="*70)
        print("RESULTS SAVED")
        print("="*70)
        print(f"Stage 1 (Parsing):   {stage1_file}")
        print(f"Stage 4 (Detection): {stage4_file}")


def print_summary(stage1_out: dict, stage4_out: dict):
    """Print analysis summary."""
    print("\n" + "="*70)
    print("FSMGuard ANALYSIS SUMMARY")
    print("="*70)
    
    # Module info
    print(f"\n📦 Module: {stage1_out['module']}")
    print(f"   States: {stage1_out['state_count']}")
    print(f"   Transitions: {stage1_out['transition_count']}")
    
    # SystemVerilog features
    if 'systemverilog_features' in stage1_out:
        sv = stage1_out['systemverilog_features']
        if sv['enum_states_found'] or sv['typedef_states_found']:
            print(f"\n✨ SystemVerilog features detected:")
            if sv['enum_states_found']:
                print(f"   ├─ Enum states: {sv['total_enum_states']}")
            if sv['typedef_states_found']:
                print(f"   └─ Typedef states: {sv['total_typedef_states']}")
    
    # Security analysis
    flagged = stage4_out.get('flagged_states', [])
    print(f"\n🔍 Security Analysis:")
    print(f"   Total states analyzed: {stage1_out['state_count']}")
    print(f"   Weak states detected: {len(flagged)}")
    
    if flagged:
        print(f"\n⚠️  VULNERABILITIES FOUND:")
        for i, state in enumerate(flagged, 1):
            risk = state.get('risk_score', 0)
            cwe = state.get('cwe', 'Unknown')
            severity = '🔴 CRITICAL' if risk >= 0.8 else '🟠 HIGH' if risk >= 0.6 else '🟡 MEDIUM'
            print(f"   {i}. {state['state_name']}")
            print(f"      Risk: {risk:.1%} | {cwe} | {severity}")
    else:
        print(f"\n✅ No critical vulnerabilities detected")
    
    print("\n" + "="*70)


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Determine parsing mode
    if args.force_sv and args.force_verilog:
        print("❌ Error: Cannot specify both --force-sv and --force-verilog")
        sys.exit(1)
    
    force_mode = 'auto'
    if args.force_sv:
        force_mode = 'systemverilog'
    elif args.force_verilog:
        force_mode = 'verilog'
    
    try:
        # Run Stage 1: Parsing
        stage1_output = run_stage1_parsing(
            args.input_file,
            force_mode=force_mode,
            verbose=args.verbose
        )
        
        # Run Stages 2-4: Analysis
        stage4_output = run_stages2_3_4(
            stage1_output,
            verbose=args.verbose
        )
        
        # Save results
        save_results(
            stage1_output,
            stage4_output,
            args.output_dir,
            verbose=args.verbose
        )
        
        # Print summary
        print_summary(stage1_output, stage4_output)
        
        # Exit with appropriate code
        if stage4_output.get('flagged_states'):
            sys.exit(2)  # Vulnerabilities found
        else:
            sys.exit(0)  # Clean
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
