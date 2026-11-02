-- M1: minimalny schemat wg sekcji 11 promptu. Kolumny sa celowo proste; rozszerzenia w kolejnych migracjach.
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE assets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    kind TEXT NOT NULL CHECK (kind IN ('image','video','audio','other')),
    abs_path TEXT,
    rel_path TEXT,
    sha256 TEXT,
    status TEXT NOT NULL DEFAULT 'present' CHECK (status IN ('present','missing','offline')),
    created_at TEXT NOT NULL
);
CREATE TABLE reference_assignments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    asset_id TEXT NOT NULL REFERENCES assets(id),
    scope TEXT NOT NULL CHECK (scope IN ('global','per_clip')),
    slot_index INTEGER NOT NULL,
    token TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE workflow_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    family TEXT NOT NULL CHECK (family IN ('h3','ltx','other')),
    fingerprint TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE scene_plans (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE generation_nodes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    parent_id TEXT REFERENCES generation_nodes(id),
    continuation_mode TEXT,
    cont_artifact_id TEXT,
    cache_identity TEXT,
    workflow_fingerprint TEXT,
    param_fingerprint TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE render_variants (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    generation_node_id TEXT REFERENCES generation_nodes(id),
    review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','accepted','rejected')),
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES render_variants(id),
    kind TEXT NOT NULL CHECK (kind IN ('raw','cumulative','new_only','preview','audio_slice','other')),
    abs_path TEXT NOT NULL,
    sha256 TEXT,
    frames INTEGER,
    fps REAL,
    created_at TEXT NOT NULL
);
CREATE TABLE timeline_items (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    variant_id TEXT REFERENCES render_variants(id),
    timeline_start_frame INTEGER NOT NULL,
    source_in_frame INTEGER NOT NULL,
    source_out_frame INTEGER NOT NULL,
    CHECK (source_out_frame > source_in_frame)
);
CREATE TABLE cues (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    start_seconds REAL NOT NULL,
    end_seconds REAL NOT NULL,
    text TEXT,
    CHECK (end_seconds > start_seconds)
);
CREATE TABLE reviews (
    id TEXT PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES render_variants(id),
    decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected')),
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE director_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    mode TEXT NOT NULL CHECK (mode IN ('manual','supervised','batch')),
    created_at TEXT NOT NULL
);
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    kind TEXT NOT NULL,
    state TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    prompt_id TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    error TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE resource_leases (
    id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES jobs(id),
    resource TEXT NOT NULL,
    holder TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    released_at TEXT
);
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    job_id TEXT,
    event TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
