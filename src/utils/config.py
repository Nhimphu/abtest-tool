import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


class Config:
    """Simple config loader with env var overrides."""

    def __init__(self, path: str | Path = "config.json") -> None:
        self._data: Dict[str, Any] = {}
        self.path = Path(path)
        self.load(self.path)

    def load(self, path: str | Path | None = None) -> None:
        p = Path(path or self.path)
        if not p.exists():
            return
        if p.suffix in {".yaml", ".yml"}:
            if yaml is None:
                return
            with p.open("r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        elif p.suffix == ".json":
            with p.open("r", encoding="utf-8") as f:
                self._data = json.load(f) or {}
        else:
            raise ValueError("Unsupported config format")

    def get(self, key: str, default: Any = None) -> Any:
        env_key = key.upper()
        if env_key in os.environ:
            return os.environ[env_key]
        return self._data.get(key, default)


config = Config()
