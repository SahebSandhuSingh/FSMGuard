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
// FSMGuard Patch - Guard Insertion
// CWE: CWE-1245
// Parameter: auth_signal
// Strictness: soft
// ============================================================
// This patch enforces access control before entering MEM_ACC
// Added by FSMGuard Stage 08 based on RL agent decision


  
  
// Soft mode: Fallback to IDLE on auth failure
always @(posedge clk) begin
    if (next_state_logic == MEM_ACC) begin
        if (auth_signal) begin
            next_state = MEM_ACC;
        end else begin
            next_state = IDLE;
        end
    end
end
  



// ============================================================
// End FSMGuard Patch
// ============================================================