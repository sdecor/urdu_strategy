from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class PositionSide(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    instrument: str
    side: PositionSide = PositionSide.FLAT
    qty: int = 0
    avg_price: Optional[float] = None

    def is_open(self) -> bool:
        return self.side != PositionSide.FLAT and self.qty > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument": self.instrument,
            "side": self.side.value if isinstance(self.side, PositionSide) else str(self.side),
            "qty": int(self.qty),
            "avg_price": self.avg_price,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Position":
        return Position(
            instrument=str(d["instrument"]),
            side=PositionSide(str(d.get("side", PositionSide.FLAT)).upper()),
            qty=int(d.get("qty", 0)),
            avg_price=float(d["avg_price"]) if d.get("avg_price") is not None else None,
        )
