from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Order:
    id: str
    instrument: str
    side: OrderSide
    qty: int
    type: OrderType = OrderType.MARKET
    client_tag: Optional[str] = None
    created_at: str = ""

    @staticmethod
    def create(instrument: str, side: OrderSide, qty: int, type: OrderType = OrderType.MARKET, client_tag: Optional[str] = None) -> "Order":
        return Order(
            id=str(uuid.uuid4()),
            instrument=instrument,
            side=side,
            qty=int(qty),
            type=type,
            client_tag=client_tag,
            created_at=_iso_now(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "instrument": self.instrument,
            "side": self.side.value if isinstance(self.side, OrderSide) else str(self.side),
            "qty": int(self.qty),
            "type": self.type.value if isinstance(self.type, OrderType) else str(self.type),
            "client_tag": self.client_tag,
            "created_at": self.created_at or _iso_now(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Order":
        return Order(
            id=str(d.get("id") or uuid.uuid4()),
            instrument=str(d["instrument"]),
            side=OrderSide(str(d["side"]).upper()),
            qty=int(d["qty"]),
            type=OrderType(str(d.get("type", OrderType.MARKET)).upper()),
            client_tag=d.get("client_tag"),
            created_at=str(d.get("created_at") or _iso_now()),
        )
