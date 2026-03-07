module sample_fsm(
    input clk,
    input reset,
    input in,
    output reg out
);

reg [1:0] state;

parameter S0 = 2'b00,
          S1 = 2'b01,
          S2 = 2'b10;

always @(posedge clk or posedge reset)
begin
    if(reset)
        state <= S0;
    else
        case(state)
            S0: if(in) state <= S1;
            S1: state <= S2;
            S2: state <= S0;
        endcase
end

endmodule