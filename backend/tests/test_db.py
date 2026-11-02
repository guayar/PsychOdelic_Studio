import sqlite3

import pytest

from psychodelic.db import connect, list_migrations, migrate


def test_migrate_creates_schema_and_is_idempotent(tmp_path):
    conn = connect(tmp_path / "s.db")
    assert migrate(conn) == [1]
    assert migrate(conn) == []  # drugie uruchomienie nic nie robi
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("projects", "assets", "jobs", "render_variants", "artifacts", "timeline_items",
              "reviews", "resource_leases", "audit_events", "schema_version"):
        assert t in tables, t
    assert conn.execute("SELECT version FROM schema_version").fetchall()[0][0] == 1


def test_migration_files_are_ordered_and_unique():
    versions = [v for v, _, _ in list_migrations()]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions)) >= 1


def test_check_constraints_reject_bad_values(tmp_path):
    conn = connect(tmp_path / "s.db")
    migrate(conn)
    conn.execute("INSERT INTO projects (id, name, root_path, created_at) VALUES ('p','n','/x','t')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO assets (id, project_id, kind, created_at) VALUES ('a','p','nieznany','t')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO timeline_items (id, project_id, timeline_start_frame, source_in_frame, source_out_frame)"
                     " VALUES ('t','p',0,10,10)")  # out musi byc > in (koniec wylaczny)


def test_foreign_keys_enforced(tmp_path):
    conn = connect(tmp_path / "s.db")
    migrate(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO assets (id, project_id, kind, created_at) VALUES ('a','brak','image','t')")
