"""
FSMGuard - Stage 8: Validation Test
===================================

Tests the patch generation system with all fix categories,
parameters, and strictness levels.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
import sys
from patch_gen import stage8_pipeline


def test_all_fix_categories():
    """
    Test all fix category combinations.
    """
    print("=" * 70)
    print("FSMGuard Stage 08 - Validation Test")
    print("=" * 70)
    print("\nTesting all fix categories, parameters, and strictness levels...\n")
    
    # Test configurations
    test_cases = [
        # Guard Insertion tests
        {
            "name": "Guard Insertion - auth_signal (soft)",
            "spec": {
                "state_name": "MEM_ACC",
                "cwe": "CWE-1245",
                "risk_score": 0.87,
                "category": 0,
                "parameter": 0,
                "strictness": 0,
                "fallback": "IDLE",
                "fix_detail": {
                    "category": "Guard Insertion",
                    "parameter": "auth_signal",
                    "strictness": "soft"
                }
            }
        },
        {
            "name": "Guard Insertion - lock_signal (strict)",
            "spec": {
                "state_name": "DEBUG",
                "cwe": "CWE-1245",
                "risk_score": 0.91,
                "category": 0,
                "parameter": 1,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "Guard Insertion",
                    "parameter": "lock_signal",
                    "strictness": "strict"
                }
            }
        },
        {
            "name": "Guard Insertion - privilege_check (strict)",
            "spec": {
                "state_name": "ADMIN",
                "cwe": "CWE-1245",
                "risk_score": 0.93,
                "category": 0,
                "parameter": 2,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "Guard Insertion",
                    "parameter": "privilege_check",
                    "strictness": "strict"
                }
            }
        },
        # Transition Pruning tests
        {
            "name": "Transition Pruning - full_removal",
            "spec": {
                "state_name": "UNSAFE",
                "cwe": "CWE-1233",
                "risk_score": 0.88,
                "category": 1,
                "parameter": 0,
                "strictness": 0,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "Transition Pruning",
                    "parameter": "full_removal",
                    "strictness": "soft"
                }
            }
        },
        {
            "name": "Transition Pruning - redirect",
            "spec": {
                "state_name": "BYPASS",
                "cwe": "CWE-1233",
                "risk_score": 0.79,
                "category": 1,
                "parameter": 1,
                "strictness": 0,
                "fallback": "IDLE",
                "fix_detail": {
                    "category": "Transition Pruning",
                    "parameter": "redirect",
                    "strictness": "soft"
                }
            }
        },
        {
            "name": "Transition Pruning - safe_redirect",
            "spec": {
                "state_name": "EXPLOIT",
                "cwe": "CWE-1233",
                "risk_score": 0.95,
                "category": 1,
                "parameter": 2,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "Transition Pruning",
                    "parameter": "safe_redirect",
                    "strictness": "strict"
                }
            }
        },
        # State Re-encoding tests
        {
            "name": "State Re-encoding - hamming",
            "spec": {
                "state_name": "EXECUTE",
                "cwe": "CWE-1298",
                "risk_score": 0.74,
                "category": 2,
                "parameter": 0,
                "strictness": 0,
                "fallback": "IDLE",
                "fix_detail": {
                    "category": "State Re-encoding",
                    "parameter": "hamming",
                    "strictness": "soft"
                }
            }
        },
        {
            "name": "State Re-encoding - parity",
            "spec": {
                "state_name": "CRITICAL",
                "cwe": "CWE-1298",
                "risk_score": 0.82,
                "category": 2,
                "parameter": 1,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "State Re-encoding",
                    "parameter": "parity",
                    "strictness": "strict"
                }
            }
        },
        {
            "name": "State Re-encoding - both",
            "spec": {
                "state_name": "SECURE",
                "cwe": "CWE-1298",
                "risk_score": 0.89,
                "category": 2,
                "parameter": 2,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "State Re-encoding",
                    "parameter": "both",
                    "strictness": "strict"
                }
            }
        },
        # Deadlock Trap tests
        {
            "name": "Deadlock Trap - alert (soft)",
            "spec": {
                "state_name": "HALT",
                "cwe": "CWE-1280",
                "risk_score": 0.65,
                "category": 3,
                "parameter": 0,
                "strictness": 0,
                "fallback": "IDLE",
                "fix_detail": {
                    "category": "Deadlock Trap",
                    "parameter": "alert",
                    "strictness": "soft"
                }
            }
        },
        {
            "name": "Deadlock Trap - lockdown (strict)",
            "spec": {
                "state_name": "STUCK",
                "cwe": "CWE-1280",
                "risk_score": 0.78,
                "category": 3,
                "parameter": 1,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "Deadlock Trap",
                    "parameter": "lockdown",
                    "strictness": "strict"
                }
            }
        },
        {
            "name": "Deadlock Trap - both (strict)",
            "spec": {
                "state_name": "FREEZE",
                "cwe": "CWE-1280",
                "risk_score": 0.92,
                "category": 3,
                "parameter": 2,
                "strictness": 1,
                "fallback": "RESET",
                "fix_detail": {
                    "category": "Deadlock Trap",
                    "parameter": "both",
                    "strictness": "strict"
                }
            }
        }
    ]
    
    # Check if input file exists
    verilog_path = "input/sample_fsm.v"
    if not os.path.exists(verilog_path):
        print(f"❌ Input file not found: {verilog_path}")
        print("\nPlease ensure the input file exists before running tests.")
        return False
    
    # Run all test cases
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'─' * 70}")
        
        try:
            # Create test-specific output directory
            test_output_dir = f"output/test_{i}"
            os.makedirs(test_output_dir, exist_ok=True)
            
            # Run Stage 8 pipeline
            result = stage8_pipeline(
                verilog_path=verilog_path,
                fix_spec=test_case['spec'],
                output_dir=test_output_dir
            )
            
            if result and "patched_file" in result and "report_file" in result:
                # Verify output files exist
                if os.path.exists(result['patched_file']) and os.path.exists(result['report_file']):
                    print(f"✅ Test {i} PASSED")
                    print(f"   Patched: {result['patched_file']}")
                    print(f"   Report:  {result['report_file']}")
                    passed += 1
                else:
                    print(f"❌ Test {i} FAILED: Output files not created")
                    failed += 1
            else:
                print(f"❌ Test {i} FAILED: Pipeline returned empty result")
                failed += 1
        
        except Exception as e:
            print(f"❌ Test {i} FAILED with exception: {e}")
            failed += 1
    
    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests:  {len(test_cases)}")
    print(f"Passed:       {passed} ✅")
    print(f"Failed:       {failed} ❌")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print("=" * 70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = test_all_fix_categories()
    sys.exit(0 if success else 1)
