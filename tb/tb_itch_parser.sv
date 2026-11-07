`timescale 1ns/1ps

module tb_itch_parser;

    //----------------------------------
    // DUT Signals
    //----------------------------------

    logic clk;
    logic rst;
    logic [7:0] data_in;
    logic data_valid;
    logic order_valid;

    logic [63:0] order_id;
    logic [31:0] shares;
    logic [31:0] price;
    logic side;

    // Instantiate DUT

    itch_parser DUT (
        .clk(clk),
        .rst(rst),
        .data_in(data_in),
        .data_valid(data_valid),

        .order_valid(order_valid),
        .order_id(order_id),
        .shares(shares),
        .price(price),
        .side(side)
    );

    // Clock generation

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Send byte task

  task send_byte(input [7:0] data);
    begin
            @(posedge clk);

            data_in <= data;
            data_valid <= 1;
            @(posedge clk);

            data_valid <= 0;

    end
    endtask

    // Test sequence

    initial
    begin
        rst = 1;
        data_in = 0;
        data_valid = 0;

        //reset

        repeat(5) @(posedge clk);

        rst = 0;

        $display("Sending ITCH Add Order");
        send_byte("A");

        // order id = 1
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h01);
        //buy
        send_byte("B");
        //100 shares
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h64);
        //price 15000

        send_byte(8'h00);
        send_byte(8'h00);
        send_byte(8'h3A);
        send_byte(8'h98);

        wait(order_valid);

        $display("---------------------------------");
        $display("ORDER RECEIVED");
        $display("---------------------------------");

        $display("Order ID = %0d", order_id);

        if(side)
            $display("Side     = BUY");
        else
            $display("Side     = SELL");

        $display("Shares   = %0d", shares);
        $display("Price    = %0d", price);

        //Self Check
        //----------------------------------

        assert(order_id == 64'd1)
            else $error("Order ID incorrect");

        assert(side == 1'b1)
            else $error("Side incorrect");

        assert(shares == 32'd100)
            else $error("Shares incorrect");

        assert(price == 32'd15000)
            else $error("Price incorrect");

        $display("");
        $display("TEST PASSED");
        $display("");

        #50;

        $finish;

    end

endmodule