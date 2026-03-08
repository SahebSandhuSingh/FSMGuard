// Fixed: Simplified interface declarations to standard ports for parser compatibility
module DmaTimingControl(
    input CLK,
    input RESET,
    input CS_N,
    input HLDA,
    input EOP_N_in,
    output reg AEN,
    output reg ADSTB,
    output IOR_N,
    output IOW_N,
    output MEMR_N,
    output MEMW_N,
    output EOP_N,
    output reg hrq,
    input VALID_DREQ0,
    input VALID_DREQ1,
    input VALID_DREQ2,
    input VALID_DREQ3,
    output reg Program,
    input [5:0] commandReg,
    input [3:0] modeReg0,
    input [3:0] modeReg1,
    input [3:0] modeReg2,
    input [3:0] modeReg3,
    input [3:0] statusReg,
    output reg ldCurrAddrTemp,
    output reg ldCurrWordTemp,
    output reg ldTempCurrAddr,
    output reg ldTempCurrWord,
    output reg enCurrAddr,
    output reg validDACK
);
	
// Internal signals
reg eop;		
reg aen;		
reg adstb;		
reg ior;		
reg iow;
reg memr;		
reg memw;	
reg checkWriteExtend;
reg checkEOP;
reg checkRead;
reg checkWrite; 

// State encoding using parameters (converted from enum for parser compatibility)
parameter iSI = 0;
parameter iS0 = 1;
parameter iS1 = 2;
parameter iS2 = 3;
parameter iS3 = 4;
parameter iS4 = 5;

// One-hot encoded states
parameter [5:0] SI = 6'b000001;
parameter [5:0] S0 = 6'b000010;
parameter [5:0] S1 = 6'b000100;
parameter [5:0] S2 = 6'b001000;
parameter [5:0] S3 = 6'b010000;
parameter [5:0] S4 = 6'b100000;

reg [5:0] state, nextstate;

always @(posedge CLK) begin
  if(RESET) begin
  	AEN    <= 1'b0;
  	ADSTB  <= 1'b0;
	state      <= SI;       // Initial FSM state
  end
  else begin
  	AEN    <= aen;
  	ADSTB  <= adstb;
	state      <= nextstate;
  end
end

  assign IOR_N = (~CS_N && HLDA) ? ior : 1'bz;       // access data from peripheral during DMA write transfer

  assign IOW_N = (~CS_N && HLDA) ? iow : 1'bz;       // load data to peripheral during DMA read transfer
	
  assign  MEMR_N = (~CS_N && HLDA) ? memr : 1'bz;   // access data from peripheral during DMA write transfer
	
  assign MEMW_N = (~CS_N && HLDA) ? memw : 1'bz;   // load data to peripheral during DMA read transfer
	
  // Fixed: Drive strength syntax corrected
  assign EOP_N = (~CS_N && HLDA) ? eop : 1'bz;

always @(*) begin
    Program = 0;  // Default
    if(!CS_N && !HLDA)      Program = 1; 
    else if(HLDA)           Program = 0;
end

always @(*) begin
    memw = 1'b1; 
    memr = 1'b1; 
    ior = 1'b1; 
    iow = 1'b1;
    
    if(checkWriteExtend) begin
        if (commandReg[5] == 1'b1 && (modeReg0[3:2] == 2'b01 || modeReg1[3:2] == 2'b01 || modeReg2[3:2] == 2'b01 || modeReg3[3:2] == 2'b01) && commandReg[0] == 1'b0)
            begin memw = 1'b0; ior = 1'b0; end   
        else    begin memw = 1'b1; ior = 1'b1; end   
    end
    else if(checkWrite) begin
        if((modeReg0[3:2] == 2'b01 || modeReg1[3:2] == 2'b01 || modeReg2[3:2] == 2'b01 || modeReg3[3:2] == 2'b01) && commandReg[0] == 1'b0) 
            begin memw = 1'b0; ior = 1'b0; end   
        else    begin memw = 1'b1; ior = 1'b1; end   
    end
    else if(checkRead) begin
        if((modeReg0[3:2] == 2'b10 || modeReg1[3:2] == 2'b10 || modeReg2[3:2] == 2'b10 || modeReg3[3:2] == 2'b10) && commandReg[0] == 1'b0)    			
            begin memr = 1'b0; iow = 1'b0; end   
        else    begin memr = 1'b1; iow = 1'b1; end  
    end 
end

always @(*) begin
if(checkEOP && statusReg[3:0]) eop = 1'b0;  
else		                   eop = 1'b1;
end

always @(*) begin   

        nextstate = state;      //default value for nextstate
              
        case(1'b1)       // reverse case       
            state[iSI]:
		       begin
		       if(VALID_DREQ0 || VALID_DREQ1 || VALID_DREQ2 || VALID_DREQ3) 	nextstate = S0;
		       else  										nextstate = SI;
		       end
		        
            state[iS0]:
		       begin
		       if(HLDA) 									nextstate = S1;
		       else if(!HLDA) 								nextstate = S0;
		       else if(!EOP_N_in) 								nextstate = SI;
		       end
		       
            state[iS1]:
		       begin
		       if(!EOP_N_in) 						        		nextstate = SI;
		       else										nextstate = S2;
		       end
		       
            state[iS2]:  
                       begin
		       if(!EOP_N_in) 						          		nextstate = SI;
                       else					  		                        nextstate = S3;
                       end

            state[iS3]:
                       begin
		       if(!EOP_N_in) 						        		nextstate = SI;
		       else										nextstate = S4;
                       end 
		       
            state[iS4]:										        nextstate = SI;
 
														
        endcase
end
	  
always @(*) begin 
{aen, adstb, checkEOP, checkRead, checkWrite, checkWriteExtend} = 6'b000000;  
{ldCurrAddrTemp, ldCurrWordTemp, ldTempCurrAddr, ldTempCurrWord, enCurrAddr, validDACK} = 6'b000000;   		 

    case(1'b1)  // reverse case

	    state[iSI]   : begin  hrq = 1'b0;  end

	    state[iS0]   : begin  hrq = 1'b1; end
		           	
	    state[iS1]   : begin  aen = 1'b1; adstb = 1'b1; validDACK = 1'b1; enCurrAddr = 1'b1; ldCurrAddrTemp= 1'b1; ldCurrWordTemp = 1'b1; hrq = 1'b1; end
        
	    state[iS2]   : begin  aen = 1'b1; adstb = 1'b0; checkRead = 1'b1; hrq = 1'b1; checkWriteExtend = 1'b1; enCurrAddr = 1'b0; ldCurrAddrTemp= 1'b0; ldCurrWordTemp = 1'b0; ldTempCurrAddr= 1'b1; ldTempCurrWord = 1'b1; end
		           	

	    state[iS3]   : begin aen = 1'b1; checkWrite = 1'b1; hrq = 1'b1; end
		
	    state[iS4]   : begin  ldTempCurrAddr= 1'b0; ldTempCurrWord = 1'b0; validDACK = 1'b0;
			       checkEOP = 1'b1; {hrq, aen} = 2'b00;
			end
					
    endcase
end
				 
endmodule
