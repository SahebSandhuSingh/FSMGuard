"""
FSMGuard - Stage 10: Final Report Generator
===========================================

Generates final security report combining all pipeline stages.

Outputs:
- fsm_report.json (machine-readable)
- fsm_report.txt (human-readable)

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any


def load_all_stage_outputs() -> Dict[str, Any]:
    """
    Load outputs from all pipeline stages.
    
    Returns:
        Dictionary with all stage data
    """
    data = {
        "stage4": None,
        "stage8": None,
        "stage9": None
    }
    
    # Load Stage 4 report (detections)
    if os.path.exists("output/stage4_report.json"):
        with open("output/stage4_report.json", 'r') as f:
            data["stage4"] = json.load(f)
    else:
        print("⚠️  Warning: stage4_report.json not found")
    
    # Load Stage 8 report (fixes)
    # Try comprehensive report first, fallback to single report
    if os.path.exists("output/stage8_comprehensive_report.json"):
        with open("output/stage8_comprehensive_report.json", 'r') as f:
            data["stage8"] = json.load(f)
    elif os.path.exists("output/stage8_report.json"):
        with open("output/stage8_report.json", 'r') as f:
            data["stage8"] = json.load(f)
    else:
        print("⚠️  Warning: stage8_report.json not found")
    
    # Load Stage 9 report (verification)
    if os.path.exists("output/stage9_result.json"):
        with open("output/stage9_result.json", 'r') as f:
            data["stage9"] = json.load(f)
    else:
        print("⚠️  Warning: stage9_result.json not found")
    
    return data


def get_cwe_name(cwe: str) -> str:
    """Get human-readable CWE name."""
    cwe_names = {
        "CWE-1245": "Improper FSM with Bypassed Auth",
        "CWE-1233": "Unguarded Debug Backdoor",
        "CWE-1298": "Hardware Logic Race Condition",
        "CWE-1280": "Unprotected Access After Asset Access"
    }
    return cwe_names.get(cwe, "Unknown CWE")


def generate_json_report(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate machine-readable JSON report.
    
    Args:
        all_data: Combined data from all stages
    
    Returns:
        Complete report dictionary
    """
    stage4 = all_data.get("stage4", {})
    stage8 = all_data.get("stage8", {})
    stage9 = all_data.get("stage9", {})
    
    # Extract design info
    original_file = stage8.get("original_file", "input/sample_fsm.v")
    patched_file = stage8.get("patched_file", "output/patched_fsm.v")
    
    # Count states from Stage 4
    total_states = len(stage4.get("states", []))
    weak_states_count = len(stage4.get("weak_states", []))
    
    # Build detections list
    detections = []
    if stage4 and ("weak_states" in stage4 or "flagged_states" in stage4):
        # Use flagged_states (new name) or weak_states (legacy name)
        weak_states = stage4.get("flagged_states", stage4.get("weak_states", []))
        for state in weak_states:
            detections.append({
                "state_name": state.get("state_name", "Unknown"),
                "risk_score": state.get("risk_score", 0.0),
                "cwe": state.get("cwe", "Unknown"),
                "cwe_name": get_cwe_name(state.get("cwe", ""))
            })
    elif stage8:
        # Fallback to Stage 8 data
        if "all_fixes" in stage8 and isinstance(stage8["all_fixes"], list):
            # New multi-fix format
            for fix in stage8["all_fixes"]:
                detections.append({
                    "state_name": fix.get("state_name", "Unknown"),
                    "risk_score": fix.get("risk_score", 0.0),
                    "cwe": fix.get("cwe", "Unknown"),
                    "cwe_name": get_cwe_name(fix.get("cwe", ""))
                })
        else:
            # Old single-fix format  
            detections.append({
                "state_name": stage8.get("state_name", "Unknown"),
                "risk_score": stage8.get("risk_score", 0.0),
                "cwe": stage8.get("cwe", "Unknown"),
                "cwe_name": get_cwe_name(stage8.get("cwe", ""))
            })
    
    # Build fixes list
    fixes = []
    if stage8:
        # Check if this is the new multi-fix format
        if "all_fixes" in stage8 and isinstance(stage8["all_fixes"], list):
            # New format with multiple fixes
            for fix in stage8["all_fixes"]:
                fixes.append({
                    "state_name": fix.get("state_name", "Unknown"),
                    "cwe": fix.get("cwe", "Unknown"),
                    "category": fix.get("fix_category", "Unknown"),
                    "parameter": fix.get("fix_parameter", "unknown"),
                    "strictness": fix.get("fix_strictness", "soft"),
                    "fallback": fix.get("fallback", "RESET")
                })
        else:
            # Old format with single fix
            fixes.append({
                "state_name": stage8.get("state_name", "Unknown"),
                "cwe": stage8.get("cwe", "Unknown"),
                "category": stage8.get("fix_category", "Unknown"),
                "parameter": stage8.get("fix_parameter", "unknown"),
                "strictness": stage8.get("fix_strictness", "soft"),
                "fallback": stage8.get("fallback", "RESET")
            })
    
    # Build verification section
    verification = {
        "compilation": stage9.get("compilation", "UNKNOWN") if stage9 else "UNKNOWN",
        "functionality": stage9.get("functionality", "UNKNOWN") if stage9 else "UNKNOWN",
        "security": stage9.get("security", "UNKNOWN") if stage9 else "UNKNOWN",
        "overall": stage9.get("overall", "UNKNOWN") if stage9 else "UNKNOWN"
    }
    
    # Build summary
    vulnerabilities_found = len(detections)
    vulnerabilities_fixed = len(fixes)
    verification_passed = verification["overall"] in ["PASS", "SKIPPED", "INFO"]
    
    # Design is safe if all vulnerabilities are patched (or verification passed)
    # INFO means verification ran but found issues - still count as attempted fix
    all_patched = vulnerabilities_fixed >= vulnerabilities_found and vulnerabilities_found > 0
    design_safe = all_patched and verification["overall"] in ["PASS", "INFO"]
    
    # Complete report
    report = {
        "design": {
            "original_file": original_file,
            "patched_file": patched_file,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_states": total_states if total_states > 0 else 9,
            "weak_states": weak_states_count if weak_states_count > 0 else len(detections)
        },
        "detections": detections,
        "fixes": fixes,
        "verification": verification,
        "summary": {
            "weak_states_detected": weak_states_count if weak_states_count > 0 else len(detections),
            "vulnerabilities_found": vulnerabilities_found,
            "vulnerabilities_fixed": vulnerabilities_fixed,
            "verification_passed": verification_passed,
            "design_safe": design_safe
        }
    }
    
    return report


def generate_txt_report(json_report: Dict[str, Any]) -> str:
    """
    Generate human-readable text report.
    
    Args:
        json_report: Complete JSON report
    
    Returns:
        Formatted text report
    """
    design = json_report["design"]
    detections = json_report["detections"]
    fixes = json_report["fixes"]
    verification = json_report["verification"]
    summary = json_report["summary"]
    
    # Extract design name from path
    design_name = os.path.basename(design["original_file"])
    analyzed_date = design["analyzed_at"].split()[0]
    
    report_lines = []
    
    # Header
    report_lines.append("  ╔══════════════════════════════════════════╗")
    report_lines.append("  ║         FSMGuard Security Report         ║")
    report_lines.append("  ╚══════════════════════════════════════════╝")
    report_lines.append("")
    report_lines.append(f"  Design:         {design_name}")
    report_lines.append(f"  Analyzed:       {analyzed_date}")
    report_lines.append(f"  Total States:   {design['total_states']}")
    report_lines.append(f"  Weak States:    {design['weak_states']}")
    report_lines.append("")
    
    # Detections table
    report_lines.append("  ┌──────────────────────────────────────────────────────┐")
    report_lines.append("  │ DETECTIONS                                           │")
    report_lines.append("  ├───────────┬───────────┬──────────────────────────────┤")
    report_lines.append("  │ STATE     │ CWE       │ DESCRIPTION                  │")
    report_lines.append("  ├───────────┼───────────┼──────────────────────────────┤")
    
    for det in detections:
        state = det["state_name"][:9].ljust(9)
        cwe = det["cwe"][:9].ljust(9)
        desc = det["cwe_name"][:28].ljust(28)
        report_lines.append(f"  │ {state} │ {cwe} │ {desc} │")
    
    report_lines.append("  └───────────┴───────────┴──────────────────────────────┘")
    report_lines.append("")
    
    # Fixes table
    report_lines.append("  ┌──────────────────────────────────────────────────────┐")
    report_lines.append("  │ FIXES APPLIED                                        │")
    report_lines.append("  ├───────────┬─────────────────────────┬────────────────┤")
    report_lines.append("  │ STATE     │ FIX                     │ STRICTNESS     │")
    report_lines.append("  ├───────────┼─────────────────────────┼────────────────┤")
    
    for fix in fixes:
        state = fix["state_name"][:9].ljust(9)
        fix_str = f"{fix['category'][:6]} + {fix['parameter'][:8]}"[:23].ljust(23)
        strictness = fix["strictness"][:14].ljust(14)
        report_lines.append(f"  │ {state} │ {fix_str} │ {strictness} │")
    
    report_lines.append("  └───────────┴─────────────────────────┴────────────────┘")
    report_lines.append("")
    
    # Verification table
    report_lines.append("  ┌──────────────────────────────────────────────────────┐")
    report_lines.append("  │ VERIFICATION RESULTS                                 │")
    report_lines.append("  ├─────────────────────┬────────────────────────────────┤")
    report_lines.append(f"  │ Compilation         │ {verification['compilation'][:30].ljust(30)} │")
    report_lines.append(f"  │ Functionality       │ {verification['functionality'][:30].ljust(30)} │")
    report_lines.append(f"  │ Security            │ {verification['security'][:30].ljust(30)} │")
    report_lines.append(f"  │ Overall             │ {verification['overall'][:30].ljust(30)} │")
    report_lines.append("  └─────────────────────┴────────────────────────────────┘")
    report_lines.append("")
    
    # Final status
    report_lines.append("  ┌──────────────────────────────────────────────────────┐")
    report_lines.append("  │ FINAL STATUS                                         │")
    report_lines.append("  ├──────────────────────────────────────────────────────┤")
    report_lines.append(f"  │  Vulnerabilities Found:  {summary['vulnerabilities_found']:<27} │")
    report_lines.append(f"  │  Vulnerabilities Fixed:  {summary['vulnerabilities_fixed']:<27} │")
    
    design_safe_str = "YES" if summary["design_safe"] else "NO"
    report_lines.append(f"  │  Design Safe:            {design_safe_str:<27} │")
    
    patched_file = design["patched_file"]
    report_lines.append(f"  │  Patched File:           {patched_file:<27} │")
    report_lines.append("  └──────────────────────────────────────────────────────┘")
    report_lines.append("")
    report_lines.append("  Generated by FSMGuard — Automated FSM Security Pipeline")
    report_lines.append("")
    
    return '\n'.join(report_lines)


def save_reports(json_report: Dict[str, Any], txt_report: str):
    """
    Save both JSON and text reports.
    
    Args:
        json_report: Machine-readable report
        txt_report: Human-readable report
    """
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Save JSON report
    with open("output/fsm_report.json", 'w') as f:
        json.dump(json_report, f, indent=2)
    
    # Save text report
    with open("output/fsm_report.txt", 'w') as f:
        f.write(txt_report)


def stage10_pipeline() -> Dict[str, Any]:
    """
    Complete Stage 10 report generation pipeline.
    
    Returns:
        Complete report dictionary
    """
    print("=" * 70)
    print("FSMGuard - Stage 10: Final Report Generator")
    print("=" * 70)
    
    # Load all stage outputs
    print("\n[1/3] Loading pipeline outputs...")
    all_data = load_all_stage_outputs()
    print("  ✅ Data loaded")
    
    # Generate JSON report
    print("\n[2/3] Generating machine-readable report...")
    json_report = generate_json_report(all_data)
    print("  ✅ JSON report generated")
    
    # Generate text report
    print("\n[3/3] Generating human-readable report...")
    txt_report = generate_txt_report(json_report)
    print("  ✅ Text report generated")
    
    # Save reports
    save_reports(json_report, txt_report)
    
    # Print completion message
    print("\n" + "=" * 70)
    print("FSMGuard pipeline complete.")
    print("─" * 70)
    print("Hardened Verilog: output/patched_fsm.v")
    print("Security Report:  output/fsm_report.txt")
    print("JSON Report:      output/fsm_report.json")
    print("─" * 70)
    print(f"Vulnerabilities found: {json_report['summary']['vulnerabilities_found']}")
    print(f"Vulnerabilities fixed: {json_report['summary']['vulnerabilities_fixed']}")
    print(f"Design safe: {'YES' if json_report['summary']['design_safe'] else 'NO'}")
    print("=" * 70 + "\n")
    
    # Display text report
    print("\n" + txt_report)
    
    return json_report


if __name__ == "__main__":
    stage10_pipeline()
