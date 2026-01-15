ALTER TABLE rationales ADD COLUMN provider_name TEXT;
ALTER TABLE rationales ADD COLUMN model_name TEXT;
ALTER TABLE rationales ADD COLUMN latency_ms INTEGER;
ALTER TABLE rationales ADD COLUMN attempts INTEGER;
ALTER TABLE rationales ADD COLUMN error TEXT;
