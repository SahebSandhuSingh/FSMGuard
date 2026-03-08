module fsm_controller(
    input clk,
    input reset,
    input login_req,
    input password_ok,
    input auth_valid,
    input auth_fail,
    output reg access_granted
);

reg [2:0] state;

localparam IDLE   = 3'b000;
localparam AUTH   = 3'b001;
localparam CHECK  = 3'b010;
localparam ACCESS = 3'b011;
localparam LOCK   = 3'b100;

always @(posedge clk or posedge reset) begin
    if(reset)
        state <= IDLE;
    else
        case(state)
            IDLE:
                if(login_req) state <= AUTH;
            AUTH:
                if(password_ok) state <= CHECK;
                else if(auth_fail) state <= LOCK;
            CHECK:
                if(auth_valid) state <= ACCESS;
                else state <= LOCK;
            ACCESS:
                state <= IDLE;
            LOCK:
                state <= IDLE;
            default:
                state <= IDLE;
        endcase
end

always @(state) begin
    access_granted = (state == ACCESS);
end

endmodule




// ============================================================
// FSMGuard Patch - State Re-encoding
// CWE: CWE-1298
// Parameter: parity
// Strictness: strict
// ============================================================
// This patch re-encodes state CRITICAL for fault resistance
// Added by FSMGuard Stage 08 based on RL agent decision


  
// Parity protection added by FSMGuard
// Detects odd number of bit flips
localparam CRITICAL_NEW = 4'b1010;  // Even parity encoding

// Parity check for CRITICAL
wire parity_CRITICAL;
assign parity_CRITICAL = ^current_state;

always @(posedge clk) begin
    if (current_state == CRITICAL) begin
        // Check parity - trigger alert on mismatch
        if (parity_CRITICAL != expected_parity) begin
            alert_signal = 1'b1;
            next_state = RESET;
        end
    end
end



// ============================================================
// End FSMGuard Patch
// ============================================================