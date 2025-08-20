from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import uuid
from typing import Any, Dict


class SignalAction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    EXIT = "EXIT"
    FLAT = "FLAT"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Signal:
    id: str
    instrument: str
    action: SignalAction
    created_at: str

    @staticmethod
    def create(instrument: str, action: SignalAction) -> "Signal":
        return Signal(id=str(uuid.uuid4()), instrument=instrument, action=action, created_at=_iso_now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "instrument": self.instrument,
            "action": self.action.value if isinstance(self.action, SignalAction) else str(self.action),
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Signal":
        return Signal(
            id=str(d["id"]),
            instrument=str(d["instrument"]),
            action=SignalAction(str(d["action"]).upper()),
            created_at=str(d.get("created_at") or _iso_now()),
        )
