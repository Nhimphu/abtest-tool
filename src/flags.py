from dataclasses import dataclass
from typing import Dict, List, Optional
import threading

@dataclass
class FeatureFlag:
    """Represents a single feature flag."""
    name: str
    enabled: bool = False
    rollout: float = 100.0  # rollout percentage 0-100

class FeatureFlagStore:
    """Thread-safe in-memory store for feature flags."""
    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.Lock()

    def create_flag(self, name: str, enabled: bool = False, rollout: float = 100.0) -> FeatureFlag:
        with self._lock:
            if name in self._flags:
                raise ValueError("Flag already exists")
            if not (0 <= rollout <= 100):
                raise ValueError("Rollout must be between 0 and 100")
            flag = FeatureFlag(name=name, enabled=enabled, rollout=rollout)
            self._flags[name] = flag
            return flag

    def update_flag(self, name: str, *, enabled: Optional[bool] = None, rollout: Optional[float] = None) -> FeatureFlag:
        with self._lock:
            if name not in self._flags:
                raise KeyError("Flag not found")
            flag = self._flags[name]
            if enabled is not None:
                flag.enabled = enabled
            if rollout is not None:
                if not (0 <= rollout <= 100):
                    raise ValueError("Rollout must be between 0 and 100")
                flag.rollout = rollout
            return flag

    def get_flag(self, name: str) -> FeatureFlag:
        with self._lock:
            if name not in self._flags:
                raise KeyError("Flag not found")
            return self._flags[name]

    def list_flags(self) -> List[FeatureFlag]:
        with self._lock:
            return list(self._flags.values())

    def delete_flag(self, name: str) -> None:
        with self._lock:
            if name in self._flags:
                del self._flags[name]
