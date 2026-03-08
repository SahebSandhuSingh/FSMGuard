# FSMGuard Stage 08 - Patch Execution

## Overview

Stage 08 is the **patch execution engine** that applies hardware security fixes to Verilog FSM designs. 

**CRITICAL DESIGN PRINCIPLE**: Stage 08 makes **ZERO security decisions**. All intelligence comes from the Stage 07 RL agent. Stage 08 is a pure template executor.

## Architecture

```
Stage 07 (RL Agent) → fix_spec → Stage 08 (Executor) → patched_fsm.v
                                                      → stage8_report.json
```

## Input: Fix Specification

The RL agent outputs a complete fix specification:

```python
fix_spec = {
    "state_name": "MEM_ACC",
    "cwe": "CWE-1245",
    "risk_score": 0.87,
    "category": 0,      # 0-3: Guard/Prune/Re-encode/Deadlock
    "parameter": 0,     # 0-2: Specific fix variant
    "strictness": 1,    # 0=soft, 1=strict
    "fallback": "RESET",
    "fix_detail": {
        "category": "Guard Insertion",
        "parameter": "auth_signal",
        "strictness": "strict"
    }
}
```

## Fix Categories

### Category 0: Guard Insertion
Adds authentication/authorization checks before state transitions.

**Parameters:**
- 0: `auth_signal` - Requires authentication
- 1: `lock_signal` - Requires security lock
- 2: `privilege_check` - Requires elevated privilege

**Strictness:**
- Soft (0): Fallback to IDLE on failure
- Strict (1): Fallback to RESET with alert

### Category 1: Transition Pruning
Removes or redirects unsafe state transitions.

**Parameters:**
- 0: `full_removal` - Block transition entirely
- 1: `redirect` - Redirect to SAFE_STATE
- 2: `safe_redirect` - Redirect with alert

### Category 2: State Re-encoding
Changes state encoding for fault resistance.

**Parameters:**
- 0: `hamming` - Hamming distance ≥ 3
- 1: `parity` - Parity protection
- 2: `both` - Hamming + parity

### Category 3: Deadlock Trap
Detects and handles deadlocked states.

**Parameters:**
- 0: `alert` - Generate alert signal
- 1: `lockdown` - Full system lockdown
- 2: `both` - Alert + lockdown

**Strictness:**
- Soft (0): Recover to IDLE
- Strict (1): Reset system

## Files

```
patch_gen.py           # Main executor
templates/
  ├── guard.j2         # Guard insertion templates
  ├── prune.j2         # Transition pruning templates
  ├── reencode.j2      # State re-encoding templates
  └── deadlock.j2      # Deadlock trap templates
```

## Usage

### Basic Usage

```python
from patch_gen import stage8_pipeline

# Load fix specification from Stage 07
fix_spec = {...}  # From RL agent

# Execute patch
result = stage8_pipeline(
    verilog_path="input/sample_fsm.v",
    fix_spec=fix_spec,
    output_dir="output"
)

# Result contains:
# {
#   "patched_file": "output/patched_fsm.v",
#   "report_file": "output/stage8_report.json"
# }
```

### Command Line

```bash
# Run demonstration
python3 patch_gen.py

# This will:
# 1. Load input/sample_fsm.v
# 2. Apply sample fix specification
# 3. Generate output/patched_fsm.v
# 4. Generate output/stage8_report.json
```

## Output Files

### Patched Verilog (`output/patched_fsm.v`)
Original Verilog code with security patch applied inline.

### Patch Report (`output/stage8_report.json`)
```json
{
  "state_name": "MEM_ACC",
  "cwe": "CWE-1245",
  "risk_score": 0.87,
  "fix_category": "Guard Insertion",
  "fix_parameter": "auth_signal",
  "fix_strictness": "strict",
  "fallback": "RESET",
  "patch_snippet": "// Verilog code...",
  "original_file": "input/sample_fsm.v",
  "patched_file": "output/patched_fsm.v"
}
```

## Template System

Stage 08 uses Jinja2 templates to generate Verilog patches. Each template:

1. Includes security property comments
2. Specifies CWE mitigation
3. Documents parameters and strictness
4. Generates syntactically correct Verilog

### Template Variables

All templates receive:
- `state_name`: Target state name
- `category`: Fix category (0-3)
- `parameter`: Fix parameter (0-2)
- `strictness`: Strictness level (0-1)
- `fallback`: Fallback state (IDLE/RESET)
- `cwe`: CWE identifier
- `risk_score`: Vulnerability score

## Integration with Pipeline

```python
# Complete FSMGuard pipeline (Stages 1-8)

# Stage 1: Parse Verilog
fsm_data = stage1_pipeline("input/design.v")

# Stage 2-3: Build graph and features
pyg_data = pipeline_stage2_stage3(fsm_data)

# Stage 4: Detect weak states
report = stage4_pipeline(pyg_data, state_names)

# Stage 5: Isolate subgraphs
subgraphs = stage5_pipeline(graph, report["weak_states"], state_names)

# Stage 6-7: RL agent selects fixes
env = FSMGuardEnv(subgraphs)
model = PPO.load("fsm_ppo_agent")
obs, _ = env.reset()
action, _ = model.predict(obs)

# Get fix specification from environment step
obs, reward, done, truncated, info = env.step(action)
fix_spec = info["fix_spec"]

# Stage 8: Execute patch
result = stage8_pipeline("input/design.v", fix_spec)
```

## Requirements

```bash
pip3 install pyverilog jinja2
```

## Key Design Principles

1. **Zero Decision Making**: Stage 08 never decides what fix to apply. It only executes what the agent decided.

2. **Template-Based**: All patches come from templates. No hardcoded security logic.

3. **Preserves Original**: Never overwrites original Verilog. Always creates new patched file.

4. **Traceable**: Every patch includes comments explaining what was changed and why.

5. **Modular**: Each fix category has its own template file for easy maintenance.

## Error Handling

Stage 08 handles errors gracefully:
- Missing Verilog file → FileNotFoundError
- Parse errors → Exception with details
- Missing templates → Template loading error
- Invalid category → ValueError
- Write failures → IOError

All errors are caught and reported without crashing the pipeline.

## Testing

```python
# Test all fix categories
test_specs = [
    {"category": 0, "parameter": 0, "strictness": 0},  # Guard soft
    {"category": 0, "parameter": 0, "strictness": 1},  # Guard strict
    {"category": 1, "parameter": 0, "strictness": 0},  # Prune
    {"category": 2, "parameter": 1, "strictness": 0},  # Re-encode
    {"category": 3, "parameter": 2, "strictness": 1},  # Deadlock
]

for spec in test_specs:
    result = stage8_pipeline("input/sample_fsm.v", spec)
    assert result is not None
```

## Next Steps

After Stage 08:
1. **Stage 09**: Formal verification of patched design
2. **Stage 10**: RTL synthesis and timing analysis
3. **Integration**: Add to CI/CD pipeline

## FAQ

**Q: Can Stage 08 apply multiple patches?**  
A: Yes, run stage8_pipeline() for each fix_spec. Patches accumulate.

**Q: What if the state doesn't exist in AST?**  
A: Stage 08 logs a warning but continues. Template is still applied.

**Q: Can I customize templates?**  
A: Yes! Edit templates/*.j2 files. Use Jinja2 syntax.

**Q: Does Stage 08 verify correctness?**  
A: No. Stage 08 only applies patches. Verification happens in Stage 09.

---

**FSMGuard Stage 08**  
Version: 1.0  
Status: ✅ Production Ready  
Date: March 7, 2026
