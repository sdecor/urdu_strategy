from typing import Optional
from pathlib import Path
import os
import yaml
from ..models.trade_state import TradeState
from ..utils.time_utils import trading_day_key


class RiskManager:
    def __init__(self, settings_path: Optional[str] = None, risk_config_path: Optional[str] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self._settings_path = settings_path or os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
        with open(self._settings_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f) or {}
        risk_path = risk_config_path or self._settings.get("config_files", {}).get("risk") or str(root / "config" / "risk.yaml")
        with open(risk_path, "r", encoding="utf-8") as f:
            self._risk_cfg = yaml.safe_load(f) or {}

        # Seuil close-all "classique"
        self._threshold = float(((self._risk_cfg.get("pnl") or {}).get("daily_close_all_when_gte") or 0.0))
        # Mode évaluation
        eval_cfg = self._risk_cfg.get("evaluation", {}) or {}
        self._eval_enabled = bool(eval_cfg.get("enabled", False))
        self._eval_daily_max = float(eval_cfg.get("daily_max_gain_usd") or 0.0)
        self._eval_reset_time = str(eval_cfg.get("reset_time_local") or "00:00")
        self._tz = str(self._settings.get("timezone") or "Europe/Zurich")

    def threshold(self) -> float:
        return self._threshold

    def evaluation_enabled(self) -> bool:
        return self._eval_enabled and self._eval_daily_max > 0

    def should_flat_all(self, state: TradeState) -> bool:
        """Retourne True si on doit clôturer toutes les positions immédiatement."""
        # Si déjà gelé aujourd'hui, on s'assure d'être flat
        if state.trading_halted_today:
            return True
        # Seuil risque classique
        if self._threshold > 0 and float(state.pnl_day) >= self._threshold:
            return True
        # Déclencheur mode évaluation (flat + halt)
        if self.evaluation_enabled() and float(state.pnl_day) >= self._eval_daily_max:
            return True
        return False

    def check_and_mark_halt(self, state: TradeState) -> bool:
        """
        Si le mode évaluation est activé et que le PnL dépasse le plafond,
        on marque la journée comme 'halted'. Renvoie True si un halt vient d'être appliqué.
        """
        if self.evaluation_enabled() and float(state.pnl_day) >= self._eval_daily_max and not state.trading_halted_today:
            state.trading_halted_today = True
            return True
        return False

    def maybe_daily_reset(self, state: TradeState) -> None:
        """Réinitialise le gel quotidien quand on passe un nouveau 'trading day' selon l'heure de reset."""
        if not self.evaluation_enabled():
            return
        key_now = trading_day_key(self._tz, self._eval_reset_time)
        if state.evaluation_reset_key != key_now:
            state.trading_halted_today = False
            state.evaluation_reset_key = key_now
