import sqlite3
from pathlib import Path

from app.config import PROJECT_ROOT, get_sqlite_path

SCHEMA_FILE = PROJECT_ROOT / "db" / "sqlite" / "001_schema.sql"
SEED_FILE = PROJECT_ROOT / "db" / "sqlite" / "002_seed.sql"


def _execute_sql_file(conn: sqlite3.Connection, sql_file: Path) -> None:
    sql = sql_file.read_text(encoding="utf-8")
    conn.executescript(sql)


def init_database(db_path: Path | None = None) -> None:
    target = db_path or get_sqlite_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        _execute_sql_file(conn, SCHEMA_FILE)
        _execute_sql_file(conn, SEED_FILE)
        conn.commit()
    finally:
        conn.close()
