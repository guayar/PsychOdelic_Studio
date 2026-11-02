"""SQLite: polaczenie, migracje z tabela schema_version, transakcje."""
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

SCHEMA_TABLE = "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
MIGRATION_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path):
    """Polaczenie w trybie autocommit. check_same_thread=False: FastAPI wykonuje endpointy w roznych watkach,
    wiec KAZDY dostep do polaczenia musi byc w blokadzie (app.state.db_lock)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def list_migrations():
    """Zwraca liste (wersja, nazwa, sql) z pakietu, posortowana po wersji."""
    out = []
    for entry in resources.files("psychodelic").joinpath("migrations").iterdir():
        m = MIGRATION_RE.match(entry.name)
        if m:
            out.append((int(m.group(1)), entry.name, entry.read_text(encoding="utf-8")))
    out.sort(key=lambda t: t[0])
    versions = [v for v, _, _ in out]
    if len(set(versions)) != len(versions):
        raise RuntimeError("zduplikowane numery migracji")
    return out


def migrate(conn):
    """Stosuje brakujace migracje. Kazda w osobnej transakcji. Zwraca liste zastosowanych wersji."""
    conn.execute(SCHEMA_TABLE)
    applied = {r[0] for r in conn.execute("SELECT version FROM schema_version")}
    done = []
    for version, name, sql in list_migrations():
        if version in applied:
            continue
        conn.execute("BEGIN IMMEDIATE")
        try:
            for stmt in _split_sql(sql):
                conn.execute(stmt)
            conn.execute("INSERT INTO schema_version(version, applied_at) VALUES (?, ?)", (version, utc_now()))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        done.append(version)
    return done


def _split_sql(sql):
    """Dzieli skrypt na pojedyncze instrukcje (bez komentarzy liniowych)."""
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    body = "\n".join(lines)
    return [s.strip() for s in body.split(";") if s.strip()]


@contextmanager
def transaction(conn):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
