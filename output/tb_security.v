
// FSMGuard Generated Testbench - Security Check
`timescale 1ns/1ps

module tb_security;
    reg clk;
    reg rst;
    reg auth_signal;
    reg lock_signal;
    reg [1:0] privilege_level;
    
    initial begin
        $display("FSMGuard Security Test");
        $display("Testing attack scenarios...");
        
        // Initialize
        clk = 0;
        rst = 1;
        auth_signal = 0;
        lock_signal = 0;
        privilege_level = 2'b00;
        
        #10 rst = 0;
        
        // Attack 1: Try to bypass auth
        $display("Attack 1: MEM_ACC bypass without auth_signal");
        auth_signal = 0;  // No auth
        #20;
        
        // Attack 2: Try to access DEBUG directly
        $display("Attack 2: Direct DEBUG access");
        #20;
        
        // Attack 3: Try to reach HALT illegally
        $display("Attack 3: Illegal HALT access");
        #20;
        
        $display("Security test completed");
        $finish;
    end
    
    // Clock generation
    always #5 clk = ~clk;
    
endmodule
