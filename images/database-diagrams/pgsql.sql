CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    created_at INT NOT NULL
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL DEFAULT '.',
    user_id INT,
    receiver_id INT,
    amount DECIMAL(15, 2) NOT NULL,
    fee DECIMAL(15, 2) NOT NULL DEFAULT 0.0,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    timestamp INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

CREATE TABLE balances (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    symbol VARCHAR(3) NOT NULL DEFAULT 'EUR',
    amount DECIMAL(15, 2) NOT NULL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE balance_history (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    symbol VARCHAR(3) NOT NULL DEFAULT 'EUR',
    amount DECIMAL(15, 2) NOT NULL DEFAULT 0.0,
    timestamp INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(3) UNIQUE NOT NULL,
    rate DECIMAL(15, 4) NOT NULL
);

CREATE TABLE exchange_rates_last_update (
    id SERIAL PRIMARY KEY,
    timestamp INT NOT NULL
);

CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    rfid_code VARCHAR(100) UNIQUE NOT NULL,
    pin_hash VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE settings (
    user_id INT PRIMARY KEY,
    language VARCHAR(2) NOT NULL DEFAULT 'en',
    default_currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    user_id INT,
    action_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'success',
    timestamp INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);