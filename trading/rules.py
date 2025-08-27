# trading/rules.py
from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Any, Dict, Iterable, Optional, Set

from utils.logger import log


class TradeRulesEngine:
    """
    Règles de trading:
    - 0 -> Flatten
    - 1 -> Long (via schedule résolu)
    - -1 -> Short (via schedule résolu)
    """
    def __init__(self, executor, inactivity_timeout: int = 5, logging_enabled: bool = True, entry_policy=None):
        self.executor = executor
        self.entry_policy = entry_policy
        self.inactivity_timeout = int(inactivity_timeout)
        self.logging_enabled = logging_enabled
        self.current_position: int = 0
        self._last_activity: datetime.datetime = datetime.datetime.now(datetime.UTC)

    def handle_signal(self, signal: Dict[str, Any]) -> None:
        self._process_signals_batch([signal])

    def tick(self) -> None:
        now = datetime.datetime.now(datetime.UTC)
        if (now - self._last_activity).total_seconds() > self.inactivity_timeout:
            self._last_activity = now

    def _process_signals_batch(self, signals: Iterable[Dict[str, Any]]) -> None:
        by_minute: Dict[str, Set[int]] = defaultdict(set)
        signals_list = list(signals)
        for s in signals_list:
            ts = s.get("timestamp", "")
            minute_key = ts[:16] if isinstance(ts, str) and len(ts) >= 16 else "unknown"
            pos = s.get("position", None)
            if pos in (-1, 0, 1):
                by_minute[minute_key].add(int(pos))

        for minute, positions in sorted(by_minute.items()):
            log(f"[RULES] Traitement des signaux pour {minute} : {positions}", self.logging_enabled)
            sample = signals_list[0] if signals_list else {}
            self._apply_positions_set(positions, signal_sample=sample)

    def _apply_positions_set(self, positions: Set[int], signal_sample: Optional[Dict[str, Any]]) -> None:
        instrument = (signal_sample or {}).get("instrument", "N/A")

        if 0 in positions:
            self._flatten_all(instrument)
        if 1 in positions:
            self._go_direction(instrument, side=0)  # long
        if -1 in positions:
            self._go_direction(instrument, side=1)  # short

        self._last_activity = datetime.datetime.now(datetime.UTC)

    def _flatten_all(self, instrument: str) -> None:
        if self.current_position != 0:
            log("[RULES] Flatten all", self.logging_enabled)
            self.executor.flatten_all(instrument)
            self.current_position = 0

    def _go_direction(self, instrument: str, side: int) -> None:
        target = 1 if side == 0 else -1
        if self.current_position == target:
            return

        schedule = None
        if self.entry_policy is not None:
            ok, reason, schedule = self.entry_policy.should_enter({"instrument": instrument, "side": "long" if side == 0 else "short"})
            if not ok:
                log(f"[ENTRY] Ignored by entry policy: {reason}", self.logging_enabled)
                return

        if schedule:
            log(f"[RULES] Entry via schedule '{schedule['id']}'", self.logging_enabled)
            placed = self.executor.place_market_with_schedule(schedule, side=side)
        else:
            log("[RULES] Entry via default config (no schedule)", self.logging_enabled)
            placed = self.executor.place_market(instrument=instrument, side=side)

        if placed:
            self.current_position = target
            if schedule and self.entry_policy is not None:
                self.entry_policy.commit_entry(schedule_id=schedule["id"])
