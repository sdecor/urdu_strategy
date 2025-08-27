# risk/risk_guard.py
from __future__ import annotations

import datetime
from typing import Dict, Any, Tuple, Optional
from utils.logger import log


def _parse_hhmm_utc(s: str) -> datetime.time:
    hh, mm = s.strip().split(":")
    return datetime.time(int(hh), int(mm), tzinfo=datetime.UTC)


def _minutes_until(now: datetime.datetime, target: datetime.time) -> int:
    """
    Minutes entre 'now' (UTC) et la prochaine occurrence de 'target' (UTC) le même jour.
    Si target est passé, renvoie un nombre négatif (écart dans le passé).
    """
    today_target = now.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    delta = today_target - now
    return int(delta.total_seconds() // 60)


class RiskGuard:
    """
    Garde-fous avant de passer un ordre:
      - 'max_order_size' : limite la taille totale d'une entrée (tous lots confondus)
      - 'min_minutes_before_stop' : refuse une nouvelle entrée si on est trop proche de 'trading_hours.stop_utc'
      - (extensible: capital max, max positions ouvertes, etc.)

    config.yaml (optionnel):
      risk:
        max_order_size: 10
        min_minutes_before_stop: 5
    """

    def __init__(self, config, logging_enabled: bool = True):
        self.config = config
        self.logging_enabled = logging_enabled
        risk_cfg: Dict[str, Any] = (getattr(config, "config", {}) or {}).get("risk", {}) or {}
        self.max_order_size: Optional[int] = risk_cfg.get("max_order_size", None)
        self.min_minutes_before_stop: Optional[int] = risk_cfg.get("min_minutes_before_stop", None)

    def can_enter(self, schedule: Dict[str, Any], side: int, total_lots: int) -> Tuple[bool, str]:
        """
        Args:
          schedule: schedule résolu (avec .id et .strategy)
          side: 0 (long) / 1 (short)
          total_lots: somme des lots à envoyer au MARKET

        Returns: (ok, reason)
        """
        # 1) taille max globale
        if self.max_order_size is not None and total_lots > int(self.max_order_size):
            reason = f"risk:max_order_size_exceeded({total_lots}>{self.max_order_size})"
            log(f"[RISK] Refus entrée: {reason}", self.logging_enabled)
            return False, reason

        # 2) proximité de l'heure stop_utc globale (si configurée)
        if self.min_minutes_before_stop is not None:
            stop_str = (getattr(self.config, "trading_hours", {}) or {}).get("stop_utc")
            if stop_str:
                now = datetime.datetime.now(datetime.UTC)
                stop_t = _parse_hhmm_utc(stop_str)
                mins = _minutes_until(now, stop_t)
                # si négatif, stop est passé; on autorise
                if mins >= 0 and mins < int(self.min_minutes_before_stop):
                    reason = f"risk:too_close_to_stop({mins}m<{self.min_minutes_before_stop}m)"
                    log(f"[RISK] Refus entrée: {reason}", self.logging_enabled)
                    return False, reason

        return True, "ok"
