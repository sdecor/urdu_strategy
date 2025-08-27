# strategy/tp_manager.py
from __future__ import annotations

from decimal import Decimal, getcontext
from typing import Optional, Dict, Any

getcontext().prec = 16  # précision suffisante pour les prix en ticks


class TPManager:
    """
    Calcule et construit un ordre LIMIT (TP) basé sur:
      - tick_size du contrat (ex: "1/32")
      - nombre de ticks (par défaut dans config.strategy.tp.ticks)
      - côté d'entrée (long -> TP sell, short -> TP buy)
      - override_ticks: permet d'overrider le nombre de ticks depuis un schedule
    """

    def __init__(self, config, logging_enabled: bool = True):
        self.config = config
        self.logging_enabled = logging_enabled

        # ticks par défaut (fallback global)
        self.ticks = int(
            ((getattr(config, "strategy", {}) or {}).get("tp", {}) or {}).get("ticks", 4)
        )

    @staticmethod
    def _parse_tick_size(value: str | float | Decimal) -> Decimal:
        """
        Accepte "1/32" ou un float/Decimal. Retourne un Decimal positif.
        """
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, Decimal):
            return value
        s = str(value).strip()
        if "/" in s:
            num, den = s.split("/", 1)
            return Decimal(num) / Decimal(den)
        return Decimal(s)

    def _get_tick_size(self, contract_id: str) -> Decimal:
        contracts = getattr(self.config, "contracts", {}) or {}
        c = contracts.get(contract_id, {}) or {}
        ts = c.get("tick_size")
        if not ts:
            # fallback raisonnable si non configuré
            return Decimal("0.01")
        return self._parse_tick_size(ts)

    def build_tp_order_payload(
        self,
        *,
        account_id: int,
        contract_id: str,
        entry_side: int,        # 0 buy (long), 1 sell (short)
        size: int,
        fill_price: float | Decimal,
        linked_order_id: Optional[int] = None,
        override_ticks: Optional[int] = None,
    ) -> Dict[str, Any]:
        if size <= 0:
            raise ValueError("TPManager: size doit être > 0")
        tick_size = self._get_tick_size(contract_id)
        ticks = int(override_ticks) if override_ticks is not None else int(self.ticks)

        fp = Decimal(str(fill_price))
        delta = tick_size * Decimal(ticks)

        if entry_side == 0:  # long -> TP sell au-dessus
            tp_price = fp + delta
            tp_side = 1
        else:  # short -> TP buy en-dessous
            tp_price = fp - delta
            tp_side = 0

        payload: Dict[str, Any] = {
            "accountId": int(account_id),
            "contractId": contract_id,
            "type": 1,  # LIMIT
            "side": int(tp_side),
            "size": int(size),
            "limitPrice": float(tp_price),
        }
        if linked_order_id is not None:
            payload["linkedOrderId"] = int(linked_order_id)
        return payload
