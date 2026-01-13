CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS rationales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    rationale_type TEXT NOT NULL,
    content TEXT NOT NULL,
    raw_data TEXT,
    FOREIGN KEY (run_id) REFERENCES runs (id)
);

ALTER TABLE recommendations ADD COLUMN run_id INTEGER;
