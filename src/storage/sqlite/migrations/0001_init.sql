CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    timeframe TEXT NOT NULL,
    action TEXT NOT NULL,
    brief TEXT NOT NULL,
    confidence REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    open_time DATETIME NOT NULL,
    expiry_seconds INTEGER NOT NULL,
    user_action TEXT NOT NULL,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations (id)
);

CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_entry_id INTEGER NOT NULL,
    close_time DATETIME NOT NULL,
    win_or_loss TEXT NOT NULL,
    comment TEXT,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries (id)
);
