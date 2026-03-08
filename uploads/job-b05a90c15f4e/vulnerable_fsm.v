module vulnerable_fsm(
    input clk,
    input reset,
    input user_input,
    input backdoor,
    output reg admin_access
);

reg [2:0] state;

localparam IDLE     = 3'b000;
localparam LOGIN    = 3'b001;
localparam USER     = 3'b010;
localparam ADMIN    = 3'b011;
localparam ERROR    = 3'b100;

always @(posedge clk or posedge reset) begin
    if(reset)
        state <= IDLE;
    else
        case(state)
            IDLE:
                // Vulnerable: Can go directly to ADMIN via backdoor (bypass authentication)
                if(backdoor) 
                    state <= ADMIN;
                else if(user_input)
                    state <= LOGIN;
                    
            LOGIN:
                // Vulnerable: Unconditional transition to USER (no password check)
                state <= USER;
                
            USER:
                // Vulnerable: Direct escalation to ADMIN without proper auth
                if(user_input)
                    state <= ADMIN;
                else
                    state <= ERROR;
                    
            ADMIN:
                // Vulnerable: Self-loop keeps admin access indefinitely
                state <= ADMIN;
                
            ERROR:
                // Goes back to IDLE
                state <= IDLE;
                
            default:
                state <= IDLE;
        endcase
end

always @(state) begin
    admin_access = (state == ADMIN);
end

endmodule
