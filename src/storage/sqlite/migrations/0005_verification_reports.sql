CREATE TABLE IF NOT EXISTS verification_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    issues_json TEXT NOT NULL,
    suggested_fix TEXT,
    policy_version TEXT NOT NULL,
    provider_name TEXT,
    model_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs (id)
);

CREATE INDEX IF NOT EXISTS idx_verification_reports_run_id ON verification_reports (run_id);
