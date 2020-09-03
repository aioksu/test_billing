DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS wallet;

CREATE TABLE wallet(
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  creation_time  DATETIME NOT NULL,
  balance DECIMAL(10,2)
);


CREATE TABLE customer(
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  creation_time DATETIME NOT NULL,
  wallet_id BIGINT NOT NULL,
  
  FOREIGN KEY (wallet_id)
    REFERENCES wallet(id)

);


CREATE TABLE logs(
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  operation_time DATETIME NOT NULL,
  session_id VARCHAR(255) NOT NULL, 
  wallet_id BIGINT DEFAULT NULL,
  current_balance DECIMAL(10,2) DEFAULT NULL,
  operation ENUM('add_money', 'transfer_to', 'transfer_from', 'create_customer') DEFAULT NULL,
  add_funds DECIMAL(10,2) DEFAULT 0,
  to_customer BIGINT  DEFAULT NULL,
  from_customer BIGINT  DEFAULT NULL,
  status ENUM('success', 'pending', 'failed') DEFAULT 'pending'
);

