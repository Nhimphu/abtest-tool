from dataclasses import dataclass
from typing import List, Optional
import threading
import sqlite3

from migrations_runner import run_migrations

@dataclass
class FeatureFlag:
    """Represents a single feature flag."""
    name: str
    enabled: bool = False
    rollout: float = 100.0  # rollout percentage 0-100

class FeatureFlagStore:
    """Thread-safe persistent store for feature flags."""

    def __init__(self, db_path: str = "flags.db"):
        self._lock = threading.Lock()
        run_migrations(db_path)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)

    def create_flag(self, name: str, enabled: bool = False, rollout: float = 100.0) -> FeatureFlag:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT 1 FROM flags WHERE name=?", (name,))
            if cur.fetchone():
                raise ValueError("Flag already exists")
            if not (0 <= rollout <= 100):
                raise ValueError("Rollout must be between 0 and 100")
            cur.execute(
                "INSERT INTO flags(name, enabled, rollout) VALUES(?,?,?)",
                (name, int(enabled), float(rollout)),
            )
            self._conn.commit()
            return FeatureFlag(name=name, enabled=enabled, rollout=rollout)

    def update_flag(self, name: str, *, enabled: Optional[bool] = None, rollout: Optional[float] = None) -> FeatureFlag:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT enabled, rollout FROM flags WHERE name=?", (name,))
            row = cur.fetchone()
            if not row:
                raise KeyError("Flag not found")
            current = FeatureFlag(name=name, enabled=bool(row[0]), rollout=row[1])
            if enabled is not None:
                current.enabled = enabled
            if rollout is not None:
                if not (0 <= rollout <= 100):
                    raise ValueError("Rollout must be between 0 and 100")
                current.rollout = rollout
            cur.execute(
                "UPDATE flags SET enabled=?, rollout=? WHERE name=?",
                (int(current.enabled), float(current.rollout), name),
            )
            self._conn.commit()
            return current

    def get_flag(self, name: str) -> FeatureFlag:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT enabled, rollout FROM flags WHERE name=?", (name,))
            row = cur.fetchone()
            if not row:
                raise KeyError("Flag not found")
            return FeatureFlag(name=name, enabled=bool(row[0]), rollout=row[1])

    def list_flags(self) -> List[FeatureFlag]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT name, enabled, rollout FROM flags")
            rows = cur.fetchall()
            return [FeatureFlag(name=r[0], enabled=bool(r[1]), rollout=r[2]) for r in rows]

    def delete_flag(self, name: str) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("DELETE FROM flags WHERE name=?", (name,))
            self._conn.commit()

    def close(self) -> None:
        """Close underlying database connection."""
        with self._lock:
            self._conn.close()
