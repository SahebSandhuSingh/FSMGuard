# SystemVerilog Support in FSMGuard

## Overview

FSMGuard now supports **SystemVerilog FSM constructs** in addition to standard Verilog. The enhanced parser automatically detects and processes SystemVerilog-specific features.

---

## ✅ Supported SystemVerilog Features

### 1. **Enum State Declarations**

```systemverilog
// Typedef enum with type specification
typedef enum logic [2:0] {
    IDLE   = 3'b000,
    FETCH  = 3'b001,
    DECODE = 3'b010,
    EXECUTE = 3'b011
} state_t;

state_t current_state, next_state;
```

```systemverilog
// Direct enum declaration
enum logic [1:0] {
    S_IDLE, S_ACTIVE, S_WAIT, S_DONE
} state;
```

### 2. **Typedef Definitions**

```systemverilog
typedef enum {RESET, RUN, HALT} fsm_state_t;
fsm_state_t current_state;
```

### 3. **Always_ff / Always_comb Blocks**

```systemverilog
// Sequential logic
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        current_state <= RESET;
    else
        current_state <= next_state;
end

// Combinational logic
always_comb begin
    case (current_state)
        IDLE:   next_state = enable ? ACTIVE : IDLE;
        ACTIVE: next_state = WAIT;
        default: next_state = IDLE;
    endcase
end
```

### 4. **Logic Data Type**

```systemverilog
logic [3:0] current_state;  // Replaces reg/wire
logic enable, reset;
```

### 5. **Unique / Priority Case Statements**

```systemverilog
unique case (state)
    IDLE:   next = ACTIVE;
    ACTIVE: next = DONE;
    DONE:   next = IDLE;
endcase

priority case (cmd)
    3'b000: out = A;
    3'b001: out = B;
    default: out = C;
endcase
```

---

## ❌ Currently NOT Supported

### Advanced SystemVerilog Features

- **Interfaces**: `interface`, `modport`
- **Classes**: `class`, `extends`, `virtual`
- **Packages**: `package`, `import`
- **Advanced assertions**: SystemVerilog Assertions (SVA)
- **Structs**: `struct`, `union`, `packed`
- **Parameterized classes**: Generic types
- **Randomization**: `randomize`, `constraint`

### Workaround

Convert these advanced features to basic enum/typedef syntax before using FSMGuard.

---

## 📖 Usage

### Automatic Detection

FSMGuard automatically detects SystemVerilog files:

```bash
python run_fsmguard.py input/fsm.sv
```

The parser checks for SystemVerilog keywords (`enum`, `typedef`, `logic`, `always_ff`, `always_comb`, `unique case`, `priority case`).

### Force SystemVerilog Parsing

```bash
python run_fsmguard.py input/fsm.v --force-sv
```

### Force Standard Verilog Parsing

```bash
python run_fsmguard.py input/fsm.sv --force-verilog
```

### Verbose Output

```bash
python run_fsmguard.py input/fsm.sv --verbose
```

Shows detected SystemVerilog features:
```
SystemVerilog Features:
  ├─ Enum states: 8
  ├─ Typedef states: 8
  └─ Parameter states: 0
```

---

## 📝 Example Input

**SystemVerilog FSM with Security Vulnerabilities:**

```systemverilog
module security_fsm (
    input logic clk, rst_n,
    input logic auth_valid,
    input logic [1:0] privilege_level,
    input logic debug_enable,
    output logic [2:0] state_out
);

    typedef enum logic [2:0] {
        RESET,
        IDLE,
        AUTH_CHECK,
        PRIVILEGED,
        MEMORY_ACC,
        DEBUG_MODE,
        ERROR
    } state_t;
    
    state_t current_state, next_state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= RESET;
        else
            current_state <= next_state;
    end
    
    always_comb begin
        unique case (current_state)
            RESET: next_state = IDLE;
            
            IDLE: begin
                if (auth_valid)
                    next_state = AUTH_CHECK;
                else if (debug_enable)
                    next_state = DEBUG_MODE;  // ⚠️ VULNERABILITY!
                else
                    next_state = IDLE;
            end
            
            AUTH_CHECK: begin
                if (privilege_level >= 2'b10)
                    next_state = PRIVILEGED;
                else
                    next_state = IDLE;
            end
            
            PRIVILEGED: next_state = MEMORY_ACC;
            
            DEBUG_MODE: begin
                // ⚠️ Can access memory from debug without auth
                next_state = MEMORY_ACC;
            end
            
            MEMORY_ACC: next_state = IDLE;
            
            default: next_state = ERROR;
        endcase
    end
    
endmodule
```

---

## 🔍 Detection Output

FSMGuard will detect:

1. **CWE-1233**: Debug state accessible without authentication
   - Path: `IDLE → DEBUG_MODE` (when `debug_enable` asserted)
   
2. **CWE-1245**: Memory access bypass
   - Path: `DEBUG_MODE → MEMORY_ACC` (skips `AUTH_CHECK` and `PRIVILEGED`)
   
3. **Privilege escalation** vulnerabilities

---

## 🛠️ Implementation Details

### Parser Architecture

```
Input File (.sv)
      ↓
[Preprocessing]
  ├─ Extract enum states (regex)
  ├─ Extract typedef definitions (regex)
  ├─ Normalize always_ff → always
  ├─ Normalize always_comb → always @(*)
  ├─ Convert logic → reg
  └─ Remove unique/priority keywords
      ↓
[Standard Verilog Parser]
  ├─ PyVerilog AST parsing
  ├─ Extract parameter states
  └─ Extract transitions
      ↓
[Merge Results]
  ├─ Combine enum + parameter states
  ├─ Remove duplicates
  └─ Generate FSM JSON
```

### File Structure

```
parser/
  ├─ parse_verilog.py          # Original Verilog parser
  ├─ parse_verilog_v2.py        # Enhanced Verilog parser
  └─ parse_systemverilog.py     # NEW: SystemVerilog wrapper

run_fsmguard.py                 # NEW: Unified CLI with auto-detection

input/
  ├─ sample_fsm.v               # Standard Verilog
  └─ systemverilog_fsm.sv       # NEW: SystemVerilog examples
```

---

## 🧪 Testing

### Test SystemVerilog Parsing

```bash
# Parse SystemVerilog FSM
python parser/parse_systemverilog.py input/systemverilog_fsm.sv output/sv_parsed.json

# Run full pipeline
python run_fsmguard.py input/systemverilog_fsm.sv --verbose
```

### Expected Output

```
[INFO] Detected SystemVerilog features in input/systemverilog_fsm.sv

======================================================================
STAGE 1: FSM PARSING
======================================================================
Input file: input/systemverilog_fsm.sv
Mode: Automatic detection

Module: security_fsm
States found: 8
Transitions found: 12
Reset state: RESET

SystemVerilog Features:
  ├─ Enum states: 8
  ├─ Typedef states: 8
  └─ Parameter states: 0

States: RESET, IDLE, AUTH_CHECK, PRIVILEGED, MEMORY_ACC, DEBUG_MODE, LOCKDOWN, ERROR

======================================================================
STAGES 2-4: GRAPH CONSTRUCTION, FEATURES & GNN DETECTION
======================================================================

⚠️  Weak states detected: 2
  ├─ DEBUG_MODE: 87.31% risk
  └─ MEMORY_ACC: 72.45% risk

======================================================================
FSMGuard ANALYSIS SUMMARY
======================================================================

📦 Module: security_fsm
   States: 8
   Transitions: 12

✨ SystemVerilog features detected:
   └─ Enum states: 8

🔍 Security Analysis:
   Total states analyzed: 8
   Weak states detected: 2

⚠️  VULNERABILITIES FOUND:
   1. DEBUG_MODE
      Risk: 87.3% | CWE-1233 | 🔴 CRITICAL
   2. MEMORY_ACC
      Risk: 72.4% | CWE-1245 | 🟠 HIGH

======================================================================
```

---

## 📚 API Reference

### `parse_systemverilog_fsm(filepath)`

Parse a SystemVerilog FSM file.

**Args:**
- `filepath` (str): Path to `.sv` or `.v` file

**Returns:**
- Dictionary with keys:
  - `module`: Module name
  - `states`: List of state names
  - `transitions`: List of transition dictionaries
  - `reset_state`: Reset state name
  - `state_count`: Number of states
  - `transition_count`: Number of transitions
  - `systemverilog_features`: Detection metadata

### `parse_fsm_automatic(filepath)`

Automatically detect file type and parse.

**Args:**
- `filepath` (str): Path to Verilog/SystemVerilog file

**Returns:**
- Same as `parse_systemverilog_fsm()`

### `is_systemverilog_file(filepath)`

Check if file contains SystemVerilog syntax.

**Args:**
- `filepath` (str): Path to file

**Returns:**
- `bool`: True if SystemVerilog features detected

---

## 🐛 Troubleshooting

### Error: "enum not recognized"

- **Cause**: PyVerilog doesn't natively support enums
- **Solution**: FSMGuard preprocesses enums using regex before parsing
- **Check**: Verify enum syntax matches examples above

### Error: "typedef not found in parsed output"

- **Cause**: Typedef may use unsupported syntax
- **Solution**: Use standard enum typedef format:
  ```systemverilog
  typedef enum logic [WIDTH] { STATES } type_name;
  ```

### States not detected from enum

- **Cause**: Enum syntax not recognized by regex parser
- **Debug**: Run with `--verbose` to see detection details
- **Workaround**: Add equivalent parameter definitions

---

## 🚀 Future Enhancements

Planned SystemVerilog features:

- [ ] `interface` parsing for FSM communication
- [ ] `struct` state encoding
- [ ] Parameterized FSM modules
- [ ] `package` import resolution
- [ ] Assertion-based vulnerability hints

---

## 📞 Support

For issues with SystemVerilog parsing:

1. Check if your syntax matches supported features (see top of doc)
2. Try `--force-verilog` to bypass SystemVerilog parsing
3. Convert advanced features to basic enum/typedef syntax
4. File issue with minimal reproducible example

---

## 📄 License

Same as FSMGuard main project.

---

**Last Updated**: March 8, 2026
**Version**: 3.0 (SystemVerilog Support Added)
