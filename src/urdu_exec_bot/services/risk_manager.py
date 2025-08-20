from pathlib import Path
from typing import Optional
import os
import yaml
from ..models.trade_state import TradeState


class RiskManager:
    def __init__(self, settings_path: Optional[str] = None, risk_config_path: Optional[str] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self._settings_path = settings_path or os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
        with open(self._settings_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f) or {}
        risk_path = risk_config_path or self._settings.get("config_files", {}).get("risk") or str(root / "config" / "risk.yaml")
        with open(risk_path, "r", encoding="utf-8") as f:
            self._risk_cfg = yaml.safe_load(f) or {}
        self._threshold = float(((self._risk_cfg.get("pnl") or {}).get("daily_close_all_when_gte") or 0.0))

    def threshold(self) -> float:
        return self._threshold

    def should_flat_all(self, state: TradeState) -> bool:
        return float(state.pnl_day) >= self._threshold if self._threshold > 0 else False
