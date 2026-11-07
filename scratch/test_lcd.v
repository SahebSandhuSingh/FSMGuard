// ======================================================================
// FSMGuard Traffic Light Controller (Verilog RTL Translation)
// ======================================================================
module fsm_controller(
    clk,
    rst,
    bNSC,
    bEWC,
    NSG,
    NSY,
    NSR,
    NSC_light,
    EWG,
    EWY,
    EWR,
    EWC_light,
    ldata,
    EN,
    RS,
    RW
);

    // ------------------------------------------------------------------
    // Port Declarations (Verilog-1995 style)
    // ------------------------------------------------------------------
    input  wire        clk;        // System Clock (50 MHz)
    input  wire        rst;        // Active-high Reset
    input  wire        bNSC;       // P3.3 - North-South Crosswalk Request
    input  wire        bEWC;       // P3.2 - East-West Crosswalk Request
    output reg         NSG;        // P1.0 - North-South Green
    output reg         NSY;        // P1.1 - North-South Yellow
    output reg         NSR;        // P1.2 - North-South Red
    output reg         NSC_light;  // P1.3 - North-South Crosswalk Indicator
    output reg         EWG;        // P1.4 - East-West Green
    output reg         EWY;        // P1.5 - East-West Yellow
    output reg         EWR;        // P1.6 - East-West Red
    output reg         EWC_light;  // P1.7 - East-West Crosswalk Indicator
    output reg  [7:0]  ldata;      // P2   - LCD Data Bus (DB7-DB0)
    output reg         EN;         // P3.7 - LCD Enable
    output reg         RS;         // P3.6 - LCD Register Select
    output reg         RW;         // P3.5 - LCD Read/Write

    // ------------------------------------------------------------------
    // FSM State Parameters (Must be declared before any procedural use)
    // ------------------------------------------------------------------
    parameter S1 = 3'd1; // EW Green  (6s)
    parameter S2 = 3'd2; // EW Yellow (2s)
    parameter S3 = 3'd3; // NS Green  (6s)
    parameter S4 = 3'd4; // NS Yellow (2s)

    // ------------------------------------------------------------------
    // Internal Registers (Must be declared before any procedural use)
    // ------------------------------------------------------------------
    reg [2:0]  presentState;
    reg [2:0]  counter;       // 6-second and 2-second countdown register
    
    reg [25:0] clk_counter;
    reg        one_sec_tick;
    
    reg        bNSC_d;
    reg        bEWC_d;
    reg        fNSC;
    reg        fEWC;
    
    reg [2:0]  lcd_step;
    reg [4:0]  char_idx;
    reg [19:0] delay_counter;

    // ------------------------------------------------------------------
    // Time Base: 1-Second Generator
    // ------------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            clk_counter  <= 0;
            one_sec_tick <= 1'b0;
        end else if (clk_counter == 50000000 - 1) begin
            clk_counter  <= 0;
            one_sec_tick <= 1'b1;
        end else begin
            clk_counter  <= clk_counter + 1;
            one_sec_tick <= 1'b0;
        end
    end

    // ------------------------------------------------------------------
    // Interrupt / Crosswalk Request Latches
    // ------------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            bNSC_d <= 1'b1;
            bEWC_d <= 1'b1;
            fNSC   <= 1'b0;
            fEWC   <= 1'b0;
        end else begin
            bNSC_d <= bNSC;
            bEWC_d <= bEWC;
            
            // Set fNSC on falling edge of button
            if (!bNSC && bNSC_d) begin
                fNSC <= 1'b1;
            end else if (presentState == S4 && one_sec_tick && counter == 0) begin
                fNSC <= 1'b0; // Cleared at the end of yellow state (State 4)
            end
            
            // Set fEWC on falling edge of button
            if (!bEWC && bEWC_d) begin
                fEWC <= 1'b1;
            end else if (presentState == S2 && one_sec_tick && counter == 0) begin
                fEWC <= 1'b0; // Cleared at the end of yellow state (State 2)
            end
        end
    end

    // ------------------------------------------------------------------
    // Traffic Light FSM Logic (Single-Always-Block Direct Transitions)
    // ------------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            presentState <= S1;
            counter      <= 6;
        end else if (one_sec_tick) begin
            if (counter == 0) begin
                case (presentState)
                    S1: begin
                        presentState <= S2;
                        counter      <= 2;
                    end
                    S2: begin
                        presentState <= S3;
                        counter      <= 6;
                    end
                    S3: begin
                        presentState <= S4;
                        counter      <= 2;
                    end
                    S4: begin
                        presentState <= S1;
                        counter      <= 6;
                    end
                    default: begin
                        presentState <= S1;
                        counter      <= 6;
                    end
                endcase
            end else begin
                counter <= counter - 1;
            end
        end
    end

    // ------------------------------------------------------------------
    // Light Control Output Logic
    // ------------------------------------------------------------------
    always @(*) begin
        // Reset defaults
        NSG       = 1'b0;
        NSY       = 1'b0;
        NSR       = 1'b1;
        NSC_light = 1'b0;
        EWG       = 1'b0;
        EWY       = 1'b0;
        EWR       = 1'b1;
        EWC_light = 1'b0;
        
        case (presentState)
            S1: begin
                NSR       = 1'b1;
                EWG       = 1'b1;
                EWR       = 1'b0;
                EWC_light = fEWC;
            end
            S2: begin
                NSR       = 1'b1;
                EWY       = 1'b1;
                EWR       = 1'b0;
            end
            S3: begin
                NSG       = 1'b1;
                NSR       = 1'b0;
                EWR       = 1'b1;
                NSC_light = fNSC;
            end
            S4: begin
                NSY       = 1'b1;
                NSR       = 1'b0;
                EWR       = 1'b1;
            end
            default: begin
                NSR = 1'b1;
                EWR = 1'b1;
            end
        endcase
    end

    // ------------------------------------------------------------------
    // synthesizable Character LCD Driver (Step-counter based sequence)
    // ------------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            lcd_step      <= 3'd0;
            char_idx      <= 0;
            delay_counter <= 0;
            EN            <= 1'b0;
            RS            <= 1'b0;
            RW            <= 1'b0;
            ldata         <= 8'h00;
        end else begin
            if (lcd_step == 3'd0) begin // LCD_INIT (Command 0x38: 8-bit, 2 lines)
                RS <= 1'b0; RW <= 1'b0; ldata <= 8'h38;
                if (delay_counter < 500) begin
                    EN <= 1'b1;
                    delay_counter <= delay_counter + 1;
                end else if (delay_counter < 1000) begin
                    EN <= 1'b0;
                    delay_counter <= delay_counter + 1;
                end else begin
                    delay_counter <= 0;
                    lcd_step <= 3'd1;
                end
            end else if (lcd_step == 3'd1) begin // LCD_CLEAR (Command 0x01: Clear Screen)
                RS <= 1'b0; RW <= 1'b0; ldata <= 8'h01;
                if (delay_counter < 500) begin
                    EN <= 1'b1;
                    delay_counter <= delay_counter + 1;
                end else if (delay_counter < 1000) begin
                    EN <= 1'b0;
                    delay_counter <= delay_counter + 1;
                end else begin
                    delay_counter <= 0;
                    lcd_step <= 3'd2;
                end
            end else if (lcd_step == 3'd2) begin // LCD_LINE1_POS (Command 0x80: Line 1 Home)
                RS <= 1'b0; RW <= 1'b0; ldata <= 8'h80;
                if (delay_counter < 500) begin
                    EN <= 1'b1;
                    delay_counter <= delay_counter + 1;
                end else if (delay_counter < 1000) begin
                    EN <= 1'b0;
                    delay_counter <= delay_counter + 1;
                end else begin
                    delay_counter <= 0;
                    lcd_step <= 3'd3;
                    char_idx <= 0;
                end
            end else if (lcd_step == 3'd3) begin // LCD_LINE1_TXT (Print text for line 1)
                RS <= 1'b1; RW <= 1'b0;
                if (presentState == S3 && fNSC) begin
                    // "Seconds NS: " + counter [0-6]
                    if (char_idx < 12) begin
                        ldata <= get_secsNS_char(char_idx);
                        if (delay_counter < 500) begin
                            EN <= 1'b1;
                            delay_counter <= delay_counter + 1;
                        end else if (delay_counter < 1000) begin
                            EN <= 1'b0;
                            delay_counter <= delay_counter + 1;
                        end else begin
                            delay_counter <= 0;
                            char_idx <= char_idx + 1;
                        end
                    end else begin
                        ldata <= 8'h30 + counter; // ASCII conversion [0-6]
                        if (delay_counter < 500) begin
                            EN <= 1'b1;
                            delay_counter <= delay_counter + 1;
                        end else if (delay_counter < 1000) begin
                            EN <= 1'b0;
                            delay_counter <= delay_counter + 1;
                        end else begin
                            delay_counter <= 0;
                            char_idx <= 0;
                            lcd_step <= 3'd4;
                        end
                    end
                end else if (presentState == S1 && fEWC) begin
                    // "Seconds EW: " + counter [0-6]
                    if (char_idx < 12) begin
                        ldata <= get_secsEW_char(char_idx);
                        if (delay_counter < 500) begin
                            EN <= 1'b1;
                            delay_counter <= delay_counter + 1;
                        end else if (delay_counter < 1000) begin
                            EN <= 1'b0;
                            delay_counter <= delay_counter + 1;
                        end else begin
                            delay_counter <= 0;
                            char_idx <= char_idx + 1;
                        end
                    end else begin
                        ldata <= 8'h30 + counter;
                        if (delay_counter < 500) begin
                            EN <= 1'b1;
                            delay_counter <= delay_counter + 1;
                        end else if (delay_counter < 1000) begin
                            EN <= 1'b0;
                            delay_counter <= delay_counter + 1;
                        end else begin
                            delay_counter <= 0;
                            char_idx <= 0;
                            lcd_step <= 3'd4;
                        end
                    end
                end else begin
                    // "Drive Safely."
                    if (char_idx < 13) begin
                        ldata <= get_warn1_char(char_idx);
                        if (delay_counter < 500) begin
                            EN <= 1'b1;
                            delay_counter <= delay_counter + 1;
                        end else if (delay_counter < 1000) begin
                            EN <= 1'b0;
                            delay_counter <= delay_counter + 1;
                        end else begin
                            delay_counter <= 0;
                            char_idx <= char_idx + 1;
                        end
                    end else begin
                        char_idx <= 0;
                        lcd_step <= 3'd4;
                    end
                end
            end else if (lcd_step == 3'd4) begin // LCD_LINE2_POS (Command 0xC0: Line 2 Home)
                RS <= 1'b0; RW <= 1'b0; ldata <= 8'hC0;
                if (delay_counter < 500) begin
                    EN <= 1'b1;
                    delay_counter <= delay_counter + 1;
                end else if (delay_counter < 1000) begin
                    EN <= 1'b0;
                    delay_counter <= delay_counter + 1;
                end else begin
                    delay_counter <= 0;
                    lcd_step <= 3'd5;
                    char_idx <= 0;
                end
            end else if (lcd_step == 3'd5) begin // LCD_LINE2_TXT (Print text for line 2)
                RS <= 1'b1; RW <= 1'b0;
                if ((presentState == S3 && fNSC) || (presentState == S1 && fEWC)) begin
                    // Leave line 2 blank during countdown
                    lcd_step <= 3'd6;
                end else begin
                    // "Look Left-Right"
                    if (char_idx < 15) begin
                        ldata <= get_warn2_char(char_idx);
                        if (delay_counter < 500) begin
                            EN <= 1'b1;
                            delay_counter <= delay_counter + 1;
                        end else if (delay_counter < 1000) begin
                            EN <= 1'b0;
                            delay_counter <= delay_counter + 1;
                        end else begin
                            delay_counter <= 0;
                            char_idx <= char_idx + 1;
                        end
                    end else begin
                        lcd_step <= 3'd6;
                    end
                end
            end else if (lcd_step == 3'd6) begin // LCD_IDLE (Wait for 1-second pulse, then redraw)
                if (one_sec_tick) begin
                    lcd_step <= 3'd1; // Clear and redraw
                end
            end
        end
    end

    // ------------------------------------------------------------------
    // Character ROM mapping helper functions (Verilog-1995 style)
    // ------------------------------------------------------------------
    function [7:0] get_warn1_char;
        input [3:0] idx;
        begin
            case(idx)
                4'd0:  get_warn1_char = "D"; 4'd1:  get_warn1_char = "r";
                4'd2:  get_warn1_char = "i"; 4'd3:  get_warn1_char = "v";
                4'd4:  get_warn1_char = "e"; 4'd5:  get_warn1_char = " ";
                4'd6:  get_warn1_char = "S"; 4'd7:  get_warn1_char = "a";
                4'd8:  get_warn1_char = "f"; 4'd9:  get_warn1_char = "e";
                4'd10: get_warn1_char = "l"; 4'd11: get_warn1_char = "y";
                4'd12: get_warn1_char = ".";
                default: get_warn1_char = " ";
            endcase
        end
    endfunction

    function [7:0] get_warn2_char;
        input [3:0] idx;
        begin
            case(idx)
                4'd0:  get_warn2_char = "L"; 4'd1:  get_warn2_char = "o";
                4'd2:  get_warn2_char = "o"; 4'd3:  get_warn2_char = "k";
                4'd4:  get_warn2_char = " "; 4'd5:  get_warn2_char = "L";
                4'd6:  get_warn2_char = "e"; 4'd7:  get_warn2_char = "f";
                4'd8:  get_warn2_char = "t"; 4'd9:  get_warn2_char = "-";
                4'd10: get_warn2_char = "R"; 4'd11: get_warn2_char = "i";
                4'd12: get_warn2_char = "g"; 4'd13: get_warn2_char = "h";
                4'd14: get_warn2_char = "t";
                default: get_warn2_char = " ";
            endcase
        end
    endfunction

    function [7:0] get_secsNS_char;
        input [3:0] idx;
        begin
            case(idx)
                4'd0:  get_secsNS_char = "S"; 4'd1:  get_secsNS_char = "e";
                4'd2:  get_secsNS_char = "c"; 4'd3:  get_secsNS_char = "o";
                4'd4:  get_secsNS_char = "n"; 4'd5:  get_secsNS_char = "d";
                4'd6:  get_secsNS_char = "s"; 4'd7:  get_secsNS_char = " ";
                4'd8:  get_secsNS_char = "N"; 4'd9:  get_secsNS_char = "S";
                4'd10: get_secsNS_char = ":"; 4'd11: get_secsNS_char = " ";
                default: get_secsNS_char = " ";
            endcase
        end
    endfunction

    function [7:0] get_secsEW_char;
        input [3:0] idx;
        begin
            case(idx)
                4'd0:  get_secsEW_char = "S"; 4'd1:  get_secsEW_char = "e";
                4'd2:  get_secsEW_char = "c"; 4'd3:  get_secsEW_char = "o";
                4'd4:  get_secsEW_char = "n"; 4'd5:  get_secsEW_char = "d";
                4'd6:  get_secsEW_char = "s"; 4'd7:  get_secsEW_char = " ";
                4'd8:  get_secsEW_char = "E"; 4'd9:  get_secsEW_char = "W";
                4'd10: get_secsEW_char = ":"; 4'd11: get_secsEW_char = " ";
                default: get_secsEW_char = " ";
            endcase
        end
    endfunction

endmodule
