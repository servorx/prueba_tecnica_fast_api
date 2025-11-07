CREATE TABLE customers ( 
    customer_id BIGINT PRIMARY KEY, 
    name VARCHAR(180) NOT NULL, 
    email VARCHAR(180), 
    phone VARCHAR(40), 
    address_line VARCHAR(255), 
    city VARCHAR(120), 
    state VARCHAR(120), 
    country VARCHAR(120), 
    postal_code VARCHAR(20) 
) ENGINE=InnoDB; 

CREATE TABLE orders ( 
    order_id BIGINT PRIMARY KEY, 
    order_date DATE NOT NULL, 
    customer_id BIGINT NOT NULL, 
    status ENUM('paid','pending','canceled') NOT NULL, 
    shipping_method ENUM('standard','express','pickup'), 
    coupon_code VARCHAR(40), 
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) 
) ENGINE=InnoDB; 

CREATE TABLE order_items ( 
    id BIGINT PRIMARY KEY AUTO_INCREMENT, 
    order_id BIGINT NOT NULL, 
    sku VARCHAR(40) NOT NULL, 
    qty INT NOT NULL, 
    unit_price DECIMAL(12,2) NOT NULL, 
    line_total DECIMAL(12,2) AS (qty * unit_price) STORED, 
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE 
) ENGINE=InnoDB; 

CREATE INDEX idx_orders_customer ON orders(customer_id); 
CREATE INDEX idx_items_order ON order_items(order_id);