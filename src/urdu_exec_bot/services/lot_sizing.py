from pathlib import Path
from typing import Optional
import os
import yaml


class LotSizing:
    def __init__(self, lots_config_path: Optional[str] = None, settings_path: Optional[str] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self._settings_path = settings_path or os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
        with open(self._settings_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f) or {}
        lots_path = lots_config_path or self._settings.get("config_files", {}).get("lots") or str(root / "config" / "instruments_lots.yaml")
        with open(lots_path, "r", encoding="utf-8") as f:
            self._lots_cfg = yaml.safe_load(f) or {}
        self._default = int((self._lots_cfg.get("lots") or {}).get("default", 1))
        self._lots = {str(k).upper(): int(v) for k, v in (self._lots_cfg.get("lots") or {}).items() if k != "default"}

    def get_qty(self, instrument: str) -> int:
        return int(self._lots.get(str(instrument).upper(), self._default))
