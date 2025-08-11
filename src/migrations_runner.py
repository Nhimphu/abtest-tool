from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)


def _get_db_path(conn: sqlite3.Connection) -> str:
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
        if row:
            return row[2]
        return ""
    except Exception as e:
        logger.debug("migrations_runner: failed to read row[2]: %s", e)
        return ""


def run_migrations(db: Union[str, sqlite3.Connection]) -> None:
    """Upgrade DB schema to the latest revision.

    Tries to use Alembic if installed. Falls back to creating tables
    directly when Alembic or SQLAlchemy are unavailable.
    """
    path: str
    if isinstance(db, sqlite3.Connection):
        path = _get_db_path(db)
        conn = db
    else:
        path = str(db)
        conn = sqlite3.connect(path)

    # Try alembic if available
    try:
        from alembic.config import Config
        from alembic import command

        cfg_path = Path(__file__).resolve().parent.parent / "alembic.ini"
        if cfg_path.exists():
            cfg = Config(str(cfg_path))
            cfg.set_main_option("script_location", str(cfg_path.parent / "alembic"))
            cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
            command.upgrade(cfg, "head")
            if not isinstance(db, sqlite3.Connection):
                conn.close()
            return
    except Exception as e:
        logger.debug(
            "migrations_runner: nothing to migrate or DB not ready: %s", e
        )
        return

    # Fallback direct table creation
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS flags (
            name TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL,
            rollout REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            test TEXT,
            result TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS session_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    if not isinstance(db, sqlite3.Connection):
        conn.close()
