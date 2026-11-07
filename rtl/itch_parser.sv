module itch_parser (

    input logic clk,
    input logic rst,

    input logic [7:0] data_in,
    input logic data_valid,

    output logic order_valid,

    output logic [63:0] order_id,
    output logic [31:0] shares,
    output logic [31:0] price,
    output logic side

);

typedef enum logic [2:0] {
    IDLE,
    GET_ID,
    GET_SIDE,
    GET_SHARES,
    GET_PRICE,
    DONE
} state_t;

state_t state;

logic [3:0] byte_count;

always_ff @( posedge clk ) begin

    if(rst)
    begin
        state <= IDLE;
        byte_count <= 0;
        order_id <= 0;
        shares <= 0;
        side <= 0;
        order_valid <= 0;
    end    
    
    else

    begin
        order_valid <= 0;
        case (state)
        IDLE: 
        begin
            if (data_valid) begin
                if(data_in == "A") begin
                    order_id <= 0;
                    shares <= 0;
                    price <= 0;
                    byte_count <= 0;
                    state <= GET_ID;
                end
            end
        end

        GET_ID:
        begin
            if(data_valid)
            begin
                order_id <= {order_id[55:0], data_in};
                if(byte_count == 7)
                begin
                    byte_count <= 0;
                    state <= GET_SIDE;
                end
                else
                begin
                    byte_count <= byte_count + 1;
                end    
            end    
        end   

        GET_SIDE:
        begin
            if(data_valid)
            begin
                side <= (data_in == "B");
                byte_count <= 0;
                state <= GET_SHARES;
            end
        end

        GET_SHARES:
        begin
            if(data_valid)
            begin
                shares <= {shares[23:0], data_in};
                if(byte_count == 3)
                begin
                    byte_count <= 0;
                    state <= GET_PRICE;
                end
                else
                begin
                    byte_count <= byte_count +1 ;
                end
            end
        end

        GET_PRICE: 
        begin
            if(data_valid) begin
                price <= {price[23:0], data_in};
                if(byte_count == 3)
                begin
                    byte_count <= 0;
                    state <= DONE;
                end
                else begin
                    byte_count <= byte_count + 1;
                end
            end
        end

        DONE:
        begin
            order_valid <= 1;
            state <= IDLE;
        end
        
        default:
        begin
            state <= IDLE;
        end
        endcase
    end
end
endmodule
