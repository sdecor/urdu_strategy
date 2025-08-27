# strategy/tp_manager.py
from decimal import Decimal
from typing import Optional, Dict, Any

from utils.price_math import parse_tick_size, add_ticks, round_to_tick


class TPManager:
    """
    Gestion du TP: calcule et construit le payload LIMIT à partir du fill.
    - Pas de hardcode: ticks et tick_size proviennent de config.yaml
    - linkedOrderId: si fourni, lie le TP à l'ordre d'entrée
    """
    def __init__(self, config, logging_enabled: bool = True):
        self.config = config
        self.logging_enabled = logging_enabled

    def _resolve_ticks(self) -> int:
        ticks = self.config.strategy.get("tp", {}).get("ticks")
        if ticks is None:
            raise ValueError("strategy.tp.ticks manquant dans config.yaml")
        return int(ticks)

    def _resolve_tick_size(self, contract_id: str) -> Decimal:
        contracts = getattr(self.config, "contracts", {}) or {}
        meta = contracts.get(contract_id) or {}
        ts = meta.get("tick_size")
        if not ts:
            raise ValueError(f"contracts.{contract_id}.tick_size manquant dans config.yaml")
        return parse_tick_size(ts)

    def build_tp_order_payload(
        self,
        *,
        account_id: int,
        contract_id: str,
        entry_side: int,
        size: int,
        fill_price: float | Decimal,
        linked_order_id: Optional[int] = None,
        override_ticks: Optional[int] = None,
    ) -> Dict[str, Any]:
        # si override_ticks est fourni, l’utiliser à la place de self.ticks

        """
        Construit le payload LIMIT pour /api/Order/place:
        - type = 1 (Limit)
        - side = opposé à entry_side
        - limitPrice = fill_price ± ticks * tick_size (arrondi grille)
        """
        ticks = self._resolve_ticks()
        tick_size = self._resolve_tick_size(contract_id)

        fill = Decimal(str(fill_price))
        tp_price = add_ticks(fill, ticks, tick_size, entry_side)
        limit_price = round_to_tick(tp_price, tick_size)

        tp_side = 1 if entry_side == 0 else 0  # long->sell, short->buy

        payload = {
            "accountId": int(account_id),
            "contractId": contract_id,
            "type": 1,              # LIMIT
            "side": tp_side,
            "size": int(size),
            "limitPrice": float(limit_price),  # envoyé en nombre
        }
        if linked_order_id is not None:
            payload["linkedOrderId"] = int(linked_order_id)
        return payload
