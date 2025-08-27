# strategy/tp_placer.py
from __future__ import annotations

from typing import Optional
from utils.logger import log
from strategy.tp_manager import TPManager
from fills.fill_resolver import FillResolver
from orders.order_sender import OrderSender


class TPPlacer:
    """
    Place un Take Profit (LIMIT) après une entrée :
      1) récupère le fill (via FillResolver)
      2) construit le payload LIMIT (via TPManager)
      3) envoie l'ordre (via OrderSender)
    """

    def __init__(self, tp_manager: TPManager, fill_resolver: FillResolver, order_sender: OrderSender, logging_enabled: bool = True):
        self.tp_manager = tp_manager
        self.fill_resolver = fill_resolver
        self.order_sender = order_sender
        self.logging_enabled = logging_enabled

    def place_tp_after_entry(
        self,
        *,
        account_id: int,
        contract_id: str,
        entry_order_id: int,
        entry_side: int,         # 0=buy (long), 1=sell (short)
        size: int,
        override_ticks: Optional[int] = None,
    ) -> bool:
        """
        Retourne True si le LIMIT TP a été placé, False sinon.
        """
        fill_price = self.fill_resolver.get_fill_price(contract_id)
        if fill_price is None:
            log("[TP] Impossible de déterminer le prix d'exécution, TP ignoré.", self.logging_enabled)
            return False

        tp_payload = self.tp_manager.build_tp_order_payload(
            account_id=account_id,
            contract_id=contract_id,
            entry_side=entry_side,
            size=size,
            fill_price=fill_price,
            linked_order_id=entry_order_id,
            override_ticks=override_ticks,
        )

        log(f"[TP] Envoi LIMIT TP -> {tp_payload}", self.logging_enabled)
        result = self.order_sender.send(tp_payload, tag="LIMIT/TP")

        if not result.get("success"):
            log(f"[TP] LIMIT échec: {result}", self.logging_enabled)
            return False

        log(f"[TP] LIMIT ok, orderId={result.get('order_id')}", self.logging_enabled)
        return True
