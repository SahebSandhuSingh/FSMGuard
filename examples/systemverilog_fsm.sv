// SystemVerilog FSM Example - Security Controller
// Demonstrates enum types, typedef, unique case, logic, always_ff/always_comb

module security_fsm (
    input clk,
    input rst_n,
    input auth_valid,
    input [1:0] privilege_level,
    input debug_enable,
    input mem_request,
    output [2:0] current_state_out
);

    // SystemVerilog typedef enum for FSM states (parsed as comments, actual states below)
    // typedef enum logic [2:0] {
    //     RESET, IDLE, AUTH_CHECK, PRIVILEGED,
    //     MEMORY_ACC, DEBUG_MODE, LOCKDOWN, ERROR
    // } state_t;
    
    // State parameters (compatible with Verilog parser)
    parameter RESET      = 3'b000;
    parameter IDLE       = 3'b001;
    parameter AUTH_CHECK = 3'b010;
    parameter PRIVILEGED = 3'b011;
    parameter MEMORY_ACC = 3'b100;
    parameter DEBUG_MODE = 3'b101;
    parameter LOCKDOWN   = 3'b110;
    parameter ERROR      = 3'b111;
    
    // State registers
    reg [2:0] current_state, next_state;

    assign current_state_out = current_state;
    
    // Sequential logic using always (Verilog-compatible)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= RESET;
        else
            current_state <= next_state;
    end
    
    // Combinational logic 
    always @(*) begin
        // Default assignment
        next_state = current_state;
        
        // State machine
        case (current_state)
            RESET: begin
                next_state = IDLE;
            end
            
            IDLE: begin
                if (auth_valid && privilege_level >= 2'b10)
                    next_state = PRIVILEGED;
                else if (auth_valid)
                    next_state = AUTH_CHECK;
                else if (debug_enable)
                    next_state = DEBUG_MODE;  // VULNERABILITY: Debug without auth
                else
                    next_state = IDLE;
            end
            
            AUTH_CHECK: begin
                if (privilege_level >= 2'b10)
                    next_state = PRIVILEGED;
                else if (mem_request)
                    next_state = MEMORY_ACC;  // VULNERABILITY: Low priv memory access
                else
                    next_state = IDLE;
            end
            
            PRIVILEGED: begin
                if (mem_request)
                    next_state = MEMORY_ACC;
                else if (!auth_valid)
                    next_state = IDLE;
                else
                    next_state = PRIVILEGED;
            end
            
            MEMORY_ACC: begin
                next_state = IDLE;
            end
            
            DEBUG_MODE: begin
                // VULNERABILITY: Can access memory from debug without auth
                if (mem_request)
                    next_state = MEMORY_ACC;
                else
                    next_state = DEBUG_MODE;  // Self-loop
            end
            
            LOCKDOWN: begin
                // Terminal state - security violation detected
                next_state = LOCKDOWN;  // Self-loop
            end
            
            ERROR: begin
                next_state = RESET;
            end
            
            default: begin
                next_state = ERROR;
            end
        endcase
    end
    
endmodule


// Alternative syntax: Simple FSM with parameters
module simple_fsm (
    input clk,
    input rst,
    input enable,
    output [1:0] state_out
);

    // State parameters 
    parameter S_IDLE   = 2'b00;
    parameter S_ACTIVE = 2'b01;
    parameter S_WAIT   = 2'b10;
    parameter S_DONE   = 2'b11;
    
    reg [1:0] state, next;
    
    assign state_out = state;
    
    always @(posedge clk) begin
        if (rst)
            state <= S_IDLE;
        else
            state <= next;
    end
    
    always @(*) begin
        case (state)
            S_IDLE:   next = enable ? S_ACTIVE : S_IDLE;
            S_ACTIVE: next = S_WAIT;
            S_WAIT:   next = S_DONE;
            S_DONE:   next = S_IDLE;
            default:  next = S_IDLE;
        endcase
    end
    
endmodule
