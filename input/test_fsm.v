// Simple ATM Controller FSM for testing FSMGuard pipeline
module atm_controller(
    input clk,
    input reset,
    input card_inserted,
    input pin_valid,
    input withdraw_req,
    input balance_ok,
    output reg cash_dispensed,
    output reg card_ejected
);

reg [2:0] state;

// State definitions
localparam IDLE        = 3'b000;
localparam CARD_READ   = 3'b001;
localparam PIN_CHECK   = 3'b010;
localparam MENU        = 3'b011;
localparam WITHDRAW    = 3'b100;
localparam DISPENSE    = 3'b101;
localparam EJECT       = 3'b110;

// State machine
always @(posedge clk or posedge reset) begin
    if (reset)
        state <= IDLE;
    else
        case(state)
            IDLE:
                if (card_inserted) state <= CARD_READ;
            
            CARD_READ:
                state <= PIN_CHECK;
            
            PIN_CHECK:
                if (pin_valid) 
                    state <= MENU;
                else 
                    state <= EJECT;
            
            MENU:
                if (withdraw_req) state <= WITHDRAW;
            
            WITHDRAW:
                // VULNERABILITY: No balance check before dispensing!
                state <= DISPENSE;
            
            DISPENSE:
                state <= EJECT;
            
            EJECT:
                state <= IDLE;
            
            default:
                state <= IDLE;
        endcase
end

// Output logic
always @(state) begin
    cash_dispensed = (state == DISPENSE);
    card_ejected = (state == EJECT);
end

endmodule
