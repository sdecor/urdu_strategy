from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping
from .position import Position, PositionSide


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TradeState:
    positions: Dict[str, Position] = field(default_factory=dict)
    pnl_day: float = 0.0
    last_reset: str = field(default_factory=_iso_now)

    def get_position(self, instrument: str) -> Position:
        if instrument not in self.positions:
            self.positions[instrument] = Position(instrument=instrument, side=PositionSide.FLAT, qty=0, avg_price=None)
        return self.positions[instrument]

    def set_position(self, p: Position) -> None:
        self.positions[p.instrument] = p

    def flat_all(self) -> None:
        for k, p in list(self.positions.items()):
            self.positions[k] = Position(instrument=p.instrument, side=PositionSide.FLAT, qty=0, avg_price=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "positions": {instr: pos.to_dict() for instr, pos in self.positions.items()},
            "pnl_day": float(self.pnl_day),
            "last_reset": self.last_reset,
        }

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "TradeState":
        positions_raw = d.get("positions", {}) or {}
        positions = {instr: Position.from_dict(pos) for instr, pos in positions_raw.items()}
        pnl_day = float(d.get("pnl_day", 0.0))
        last_reset = str(d.get("last_reset") or _iso_now())
        return TradeState(positions=positions, pnl_day=pnl_day, last_reset=last_reset)
