-- M3: pola osi montazowej potrzebne do eksportu (identyfikator klipu i sciezka wzgledna artefaktu).
ALTER TABLE timeline_items ADD COLUMN clip_id TEXT;
ALTER TABLE timeline_items ADD COLUMN source_path TEXT;
