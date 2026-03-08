// Network Protocol State Machine - Security Example
// Has multiple vulnerabilities for FSMGuard testing
module network_protocol(
    input clk,
    input reset,
    input syn_received,
    input auth_valid,
    input data_ready,
    input admin_mode,
    input timeout,
    output reg connected,
    output reg authenticated,
    output reg data_transfer
);

reg [2:0] state;

// State definitions
localparam IDLE         = 3'b000;
localparam SYN_WAIT     = 3'b001;
localparam AUTH         = 3'b010;
localparam CONNECTED    = 3'b011;
localparam DATA_XFER    = 3'b100;
localparam ADMIN        = 3'b101;
localparam DISCONNECT   = 3'b110;

// State machine
always @(posedge clk or posedge reset) begin
    if (reset)
        state <= IDLE;
    else
        case(state)
            IDLE:
                if (syn_received) state <= SYN_WAIT;
            
            SYN_WAIT:
                // VULNERABILITY 1: Can jump to CONNECTED without AUTH
                if (admin_mode) 
                    state <= ADMIN;  // Backdoor bypass!
                else
                    state <= AUTH;
            
            AUTH:
                if (auth_valid)
                    state <= CONNECTED;
                else if (timeout)
                    state <= DISCONNECT;
            
            CONNECTED:
                if (data_ready)
                    state <= DATA_XFER;
                else if (timeout)
                    state <= DISCONNECT;
            
            DATA_XFER:
                // VULNERABILITY 2: No timeout or bounds check
                if (!data_ready)
                    state <= CONNECTED;
            
            ADMIN:
                // VULNERABILITY 3: Admin can access anything without auth check
                if (data_ready)
                    state <= DATA_XFER;
                else
                    state <= CONNECTED;
            
            DISCONNECT:
                state <= IDLE;
            
            default:
                state <= IDLE;
        endcase
end

// Output logic
always @(state) begin
    connected = (state == CONNECTED) || (state == DATA_XFER) || (state == ADMIN);
    authenticated = (state == AUTH) || (state == CONNECTED) || (state == DATA_XFER);
    data_transfer = (state == DATA_XFER);
end

endmodule
