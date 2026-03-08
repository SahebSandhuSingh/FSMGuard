import json

print("="*70)
print("VULNERABILITY DETECTION & RESOLUTION ANALYSIS")
print("="*70)

# Load analysis results
with open('output/stage4_report.json', 'r') as f:
    stage4 = json.load(f)

with open('output/stage8_report.json', 'r') as f:
    stage8 = json.load(f)

print("\n📊 ORIGINAL DESIGN VULNERABILITY:")
print("-" * 70)
print("State: WITHDRAW")
print("Issue: Transitions to DISPENSE without checking 'balance_ok' signal")
print("Code: state <= DISPENSE;  // Missing: if (balance_ok)")
print("Risk: Allows cash dispensing regardless of account balance")
print("CWE: Should be CWE-863 (Incorrect Authorization)")

print("\n🔍 STAGE 4 DETECTION RESULTS:")
print("-" * 70)
print(f"Total States: {stage4['total_states']}")
print(f"Weak States Detected: {stage4['weak_states_found']}\n")

for i, state in enumerate(stage4['flagged_states'], 1):
    marker = "⚠️ ACTUAL VULN" if state['state_name'] == 'WITHDRAW' else ""
    print(f"{i}. {state['state_name']:<12} | Risk: {state['risk_score']:.3f} | {state['cwe']} {marker}")
    if state['state_name'] == 'WITHDRAW':
        print(f"   Features: auth_bypass={state['features']['auth_bypass']}, " +
              f"guarded={state['features']['guarded']}")

print("\n🔧 STAGE 6-7 AGENT DECISION:")
print("-" * 70)
print(f"State Fixed: {stage8['state_name']}")
print(f"Fix Applied: {stage8['fix_category']} + {stage8['fix_parameter']} ({stage8['fix_strictness']})")
print(f"CWE: {stage8['cwe']}")

print("\n❌ PROBLEM IDENTIFIED:")
print("-" * 70)
print("✗ Agent fixed: IDLE (not the vulnerable state)")
print("✗ WITHDRAW remains unfixed (still missing balance check)")
print("✗ Vulnerability STILL EXISTS in patched design")

print("\n💡 ROOT CAUSE:")
print("-" * 70)
print("1. Stage 4 correctly detected WITHDRAW as weak (auth_bypass=1.0)")
print("2. But pipeline only fixes FIRST weak state (IDLE)")
print("3. Should prioritize by risk_score or fix ALL weak states")

print("\n🎯 RECOMMENDATIONS:")
print("-" * 70)
print("Option A: Fix ALL detected weak states (not just first)")
print("Option B: Sort by risk_score and fix highest risk first")
print("Option C: Let agent decide which state to prioritize")
print("\nCurrent: IDLE (0.476) was fixed")
print("Should fix: CARD_READ (0.492) - highest risk")
print("Or fix: WITHDRAW (0.429) - the actual known vulnerability")

print("\n" + "="*70)
