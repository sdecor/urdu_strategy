import json
import os
import tempfile
from pathlib import Path
from typing import Optional
import yaml
from ..models.trade_state import TradeState


class StateStore:
    def __init__(self, settings_path: Optional[str] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self._settings_path = settings_path or os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
        with open(self._settings_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f) or {}
        state_cfg = self._settings.get("paths", {}).get("state", {})
        self._state_path = Path(state_cfg.get("trade_state") or (root / "state" / "trade_state.json"))
        self._offset_path = Path(state_cfg.get("offset") or (root / "state" / "offsets" / "signals.offset"))
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._offset_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> TradeState:
        if not self._state_path.exists():
            return TradeState()
        with open(self._state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TradeState.from_dict(data)

    def save(self, state: TradeState) -> None:
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(self._state_path.parent), prefix=".tmp_trade_state_", text=True)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmpf:
                json.dump(state.to_dict(), tmpf, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._state_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def read_offset(self) -> int:
        if not self._offset_path.exists():
            return 0
        try:
            with open(self._offset_path, "r", encoding="utf-8") as f:
                return int(f.read().strip() or "0")
        except Exception:
            return 0

    def write_offset(self, offset: int) -> None:
        self._offset_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._offset_path, "w", encoding="utf-8") as f:
            f.write(str(int(offset)))
