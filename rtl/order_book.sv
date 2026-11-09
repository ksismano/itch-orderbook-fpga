module order_book
  (
    input logic clk,
    input logic rst,
    input logic order_valid,
    input logic [63:0] order_id,
    input logic side,
    input logic [31:0] shares,
    input logic [31:0] price
  );
  
