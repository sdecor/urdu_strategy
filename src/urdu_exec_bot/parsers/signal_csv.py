from typing import Optional, Dict, Any
from ..models.signal import Signal, SignalAction


class SignalCsvParser:
    def __init__(self, settings: Dict[str, Any]) -> None:
        csv_cfg = settings.get("csv_reader", {}) or {}
        self._delimiter = str(csv_cfg.get("delimiter", ","))
        self._schema = list(csv_cfg.get("schema") or ["instrument", "action"])
        self._mapping = {str(k).lower(): str(v).upper() for k, v in (csv_cfg.get("action_mapping") or {}).items()}

    def parse_line(self, line: str) -> Optional[Signal]:
        raw = [c.strip() for c in line.strip().split(self._delimiter)]
        if not raw or all(x == "" for x in raw):
            return None
        cols = {self._schema[i]: raw[i] if i < len(raw) else "" for i in range(len(self._schema))}
        instrument = cols.get("instrument", "").upper()
        action_raw = cols.get("action", "")
        mapped = self._mapping.get(action_raw.lower(), action_raw).upper()
        if mapped not in ("LONG", "SHORT", "EXIT"):
            return None
        action = SignalAction[mapped]
        return Signal.create(instrument=instrument, action=action)
