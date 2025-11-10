CREATE TABLE IF NOT EXISTS cash_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('IN', 'OUT')),
    amount REAL NOT NULL CHECK(amount > 0),
    category TEXT NOT NULL,
    description TEXT,
    reference_id INTEGER,
    reference_type TEXT,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cash_balance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    balance REAL NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cash_trans_date ON cash_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_cash_trans_type ON cash_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_cash_trans_category ON cash_transactions(category);

INSERT INTO cash_balance (balance) 
SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM cash_balance);
