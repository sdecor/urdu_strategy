# orders/order_builder.py
from __future__ import annotations
from typing import Optional, Dict, Any


class OrderBuilder:
    """
    Construit des payloads TopstepX propres (sans hardcode) à partir de la config.
    - Market
    - Limit
    (Extensible: Stop, TrailingStop, etc.)
    """

    def __init__(self, config):
        self.config = config

    def _account_id(self, account_id: Optional[int]) -> int:
        return int(account_id if account_id is not None else self.config.account_id)

    def _contract_id(self, contract_id: Optional[str]) -> str:
        cid = contract_id if contract_id is not None else getattr(self.config, "contract_id", None)
        if not cid:
            raise ValueError("OrderBuilder: contract_id manquant (vérifie config.contract_id).")
        return cid

    # ------------ Market ------------
    def build_market_order(
        self,
        *,
        side: int,                        # 0 = buy (long), 1 = sell (short)
        size: int,
        account_id: Optional[int] = None,
        contract_id: Optional[str] = None,
        order_type: Optional[int] = None  # fallback = config.default_order_type (attendu 2)
    ) -> Dict[str, Any]:
        if size <= 0:
            raise ValueError("OrderBuilder: size doit être > 0 pour un MARKET.")

        payload = {
            "accountId": self._account_id(account_id),
            "contractId": self._contract_id(contract_id),
            "type": int(order_type if order_type is not None else getattr(self.config, "default_order_type", 2)),
            "side": int(side),
            "size": int(size),
        }
        return payload

    # ------------ Limit ------------
    def build_limit_order(
        self,
        *,
        side: int,                        # 0 = buy, 1 = sell
        size: int,
        limit_price: float,
        account_id: Optional[int] = None,
        contract_id: Optional[str] = None,
        linked_order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        if size <= 0:
            raise ValueError("OrderBuilder: size doit être > 0 pour un LIMIT.")
        if limit_price is None:
            raise ValueError("OrderBuilder: limit_price est requis pour un LIMIT.")

        payload = {
            "accountId": self._account_id(account_id),
            "contractId": self._contract_id(contract_id),
            "type": 1,  # LIMIT
            "side": int(side),
            "size": int(size),
            "limitPrice": float(limit_price),
        }
        if linked_order_id is not None:
            payload["linkedOrderId"] = int(linked_order_id)
        return payload
