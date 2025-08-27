import datetime
import json
import os
from typing import Dict, Optional

class FileSessionStorage:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def load(self) -> Dict:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save(self, state: Dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)


class SessionGate:
    def __init__(self, windows_config: Dict, storage: FileSessionStorage, logging_enabled: bool = True):
        self.windows = windows_config or {}
        self.storage = storage
        self.state = self.storage.load()
        self.logging_enabled = logging_enabled

    def _now_utc(self) -> datetime.datetime:
        # timezone-aware
        return datetime.datetime.now(datetime.UTC)

    def current_window_id(self) -> Optional[str]:
        now = self._now_utc().time()
        for win_id, win in self.windows.items():
            start = datetime.time.fromisoformat(win["start_utc"])
            end = datetime.time.fromisoformat(win["end_utc"])
            if start <= now <= end:
                return win_id
        return None

    def can_enter(self, win_id: str) -> bool:
        quota = self.windows.get(win_id, {}).get("max_trades", 0)
        today = self._now_utc().date().isoformat()
        key = f"{today}:{win_id}"
        used = self.state.get(key, 0)
        return used < quota

    def commit_entry(self, win_id: str):
        today = self._now_utc().date().isoformat()
        key = f"{today}:{win_id}"
        self.state[key] = self.state.get(key, 0) + 1
        self.storage.save(self.state)
