import time
from collections import defaultdict
from utils.logger import log
from utils.state import STATE


class TradeRulesEngine:
    def __init__(self, executor, inactivity_timeout=5, logging_enabled=True):
        self.executor = executor
        self.signals_per_minute = defaultdict(list)
        self.last_signal_time = time.time()
        self.last_processed_minute = None
        self.inactivity_timeout = inactivity_timeout
        self.current_position = 0  # 0: flat, 1: long, -1: short
        self.logging_enabled = logging_enabled
        STATE.set_position(self.current_position)

    def _get_minute_key(self, timestamp_str):
        return timestamp_str[:16]

    def handle_signal(self, signal: dict):
        minute_key = self._get_minute_key(signal["timestamp"])
        self.signals_per_minute[minute_key].append(signal)
        self.last_signal_time = time.time()
        STATE.record_signal(signal)

    def tick(self):
        now = time.time()
        if now - self.last_signal_time < self.inactivity_timeout:
            return
        if not self.signals_per_minute:
            return

        latest_minute = max(self.signals_per_minute.keys())
        if latest_minute == self.last_processed_minute:
            return

        signals = self.signals_per_minute[latest_minute]
        self._process_minute_signals(latest_minute, signals)
        self.last_processed_minute = latest_minute
        del self.signals_per_minute[latest_minute]

    def _process_minute_signals(self, minute_key, signals):
        positions = set(s["position"] for s in signals)
        instrument = signals[0]["instrument"]
        log(f"[RULES] Traitement des signaux pour {minute_key} : {positions}", self.logging_enabled)

        if positions == {0, 1}:
            self._flatten_all(instrument)
            self._go_long(instrument)
        elif positions == {0, -1}:
            self._flatten_all(instrument)
            self._go_short(instrument)
        elif len(signals) == 1:
            pos = signals[0]["position"]
            if pos == 0:
                self._flatten_all(instrument)
            elif pos == 1:
                if self.current_position == 1:
                    self._go_long(instrument)
                else:
                    self._flatten_all(instrument)
                    self._go_long(instrument)
            elif pos == -1:
                if self.current_position == -1:
                    self._go_short(instrument)
                else:
                    self._flatten_all(instrument)
                    self._go_short(instrument)
        else:
            log(f"[RULES] Aucun pattern reconnu pour {minute_key}, aucun trade déclenché.", self.logging_enabled)

    def _flatten_all(self, instrument):
        if self.current_position != 0:
            log("[RULES] Flatten all", self.logging_enabled)
            STATE.record_action("flatten", instrument)
            self.executor.flatten_all(instrument)
            self.current_position = 0
            STATE.set_position(0)

    def _go_long(self, instrument):
        log("[RULES] Long +1", self.logging_enabled)
        STATE.record_action("long+1", instrument)
        self.executor.process_signal({"instrument": instrument, "position": 1})
        self.current_position = 1
        STATE.set_position(1)

    def _go_short(self, instrument):
        log("[RULES] Short -1", self.logging_enabled)
        STATE.record_action("short-1", instrument)
        self.executor.process_signal({"instrument": instrument, "position": -1})
        self.current_position = -1
        STATE.set_position(-1)
