import csv
import io
import re
from typing import Optional, Dict, Any, Tuple
from ..models.signal import Signal, SignalAction


class SignalCsvParser:
    def __init__(self, settings: Dict[str, Any]) -> None:
        csv_cfg = settings.get("csv_reader", {}) or {}
        self._delimiter = str(csv_cfg.get("delimiter", ","))
        self._schema = list(csv_cfg.get("schema") or ["received_at", "content_type", "raw"])
        self._mapping = {str(k).lower(): str(v).upper() for k, v in (csv_cfg.get("action_mapping") or {}).items()}

    def _parse_csv_line(self, line: str) -> Optional[Dict[str, str]]:
        f = io.StringIO(line)
        try:
            row = next(csv.reader(f, delimiter=self._delimiter))
        except StopIteration:
            return None
        cols = {self._schema[i]: (row[i] if i < len(row) else "") for i in range(len(self._schema))}
        # Skip header
        if cols.get(self._schema[0], "").lower() == self._schema[0].lower():
            return None
        return cols

    def _extract_from_raw(self, text: str) -> Optional[Tuple[str, SignalAction]]:
        if not text:
            return None
        t = text.replace("\u202f", " ").replace("\xa0", " ")
        # Try "nouvelle position ... est (-1|0|1)"
        mpos = re.search(r"nouvelle\s+position.*?est\s+(-?\d+)", t, flags=re.IGNORECASE | re.DOTALL)
        instrument = None
        minst = re.search(r"sur\s+([A-Za-z0-9!._\-]+)", t, flags=re.IGNORECASE)
        if minst:
            instrument = minst.group(1).upper()
        if mpos:
            val = int(mpos.group(1))
            if val > 0:
                return (instrument or "", SignalAction.LONG)
            if val < 0:
                return (instrument or "", SignalAction.SHORT)
            return (instrument or "", SignalAction.FLAT)
        # Fallback to "ordre buy/sell"
        mact = re.search(r"ordre\s+(buy|sell)\b", t, flags=re.IGNORECASE)
        if mact:
            act = mact.group(1).lower()
            mapped = self._mapping.get(act, "LONG" if act == "buy" else "SHORT")
            action = SignalAction[mapped]
            return (instrument or "", action)
        return None

    def parse_line(self, line: str) -> Optional[Signal]:
        cols = self._parse_csv_line(line)
        if not cols:
            return None
        raw = cols.get("raw", "")
        extracted = self._extract_from_raw(raw)
        if not extracted:
            return None
        instrument, action = extracted
        if not instrument:
            return None
        return Signal.create(instrument=instrument, action=action)
