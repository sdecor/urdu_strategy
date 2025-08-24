import threading
from collections import deque
from datetime import datetime


class BotState:
    def __init__(self, max_items=200):
        self._lock = threading.Lock()
        self.current_position = 0
        self.recent_signals = deque(maxlen=max_items)
        self.recent_actions = deque(maxlen=max_items)
        self.trade_events = deque(maxlen=max_items)

    def set_position(self, pos: int):
        with self._lock:
            self.current_position = pos

    def record_signal(self, signal: dict):
        with self._lock:
            self.recent_signals.appendleft({
                "ts": datetime.utcnow().isoformat() + "Z",
                "signal": signal
            })

    def record_action(self, action_type: str, instrument: str):
        with self._lock:
            self.recent_actions.appendleft({
                "ts": datetime.utcnow().isoformat() + "Z",
                "action": action_type,
                "instrument": instrument
            })

    def record_trade_event(self, instrument: str, position: int, quantity: int, result: dict | None):
        with self._lock:
            self.trade_events.appendleft({
                "ts": datetime.utcnow().isoformat() + "Z",
                "instrument": instrument,
                "position": position,
                "quantity": quantity,
                "result": result
            })

    def snapshot(self):
        with self._lock:
            return {
                "current_position": self.current_position,
                "signals": list(self.recent_signals),
                "actions": list(self.recent_actions),
                "trades": list(self.trade_events),
            }


STATE = BotState()
