# strategy/schedule_executor.py
from __future__ import annotations

from typing import Dict, Any, Optional

from utils.logger import log
from orders.order_builder import OrderBuilder
from orders.order_sender import OrderSender
from strategy.tp_placer import TPPlacer
from risk.risk_guard import RiskGuard


class ScheduleExecutor:
    """
    Exécute une entrée selon un 'schedule' résolu :
      - RiskGuard.can_enter(...)
      - Place MARKET pour 'total_lots'
      - Pose un LIMIT TP pour 'tp_lots' (si > 0)
      - Laisse le reste ouvert si 'carry_remaining' = True
    """

    def __init__(
        self,
        *,
        config,
        order_builder: OrderBuilder,
        order_sender: OrderSender,
        tp_placer: TPPlacer,
        risk_guard: Optional[RiskGuard] = None,
        logging_enabled: bool = True
    ):
        self.config = config
        self.order_builder = order_builder
        self.order_sender = order_sender
        self.tp_placer = tp_placer
        self.risk_guard = risk_guard or RiskGuard(config, logging_enabled=logging_enabled)
        self.logging_enabled = logging_enabled

    def execute(self, schedule: Dict[str, Any], side: int) -> bool:
        contract_id = getattr(self.config, "contract_id", None)
        if not contract_id:
            log("[SCHEDULE-EXEC] contract_id manquant dans config.", self.logging_enabled)
            return False

        strat = (schedule or {}).get("strategy", {}) or {}
        total_lots = int(strat.get("total_lots", getattr(self.config, "default_quantity", 1)))
        tp_lots = int(strat.get("tp_lots", total_lots))
        override_ticks: Optional[int] = strat.get("tp_ticks", None)
        carry_remaining = bool(strat.get("carry_remaining", False))

        if total_lots <= 0:
            log("[SCHEDULE-EXEC] total_lots invalide (<=0)", self.logging_enabled)
            return False
        if tp_lots < 0 or tp_lots > total_lots:
            log("[SCHEDULE-EXEC] tp_lots invalide (0..total_lots)", self.logging_enabled)
            return False

        # 🔒 Risk checks
        ok, reason = self.risk_guard.can_enter(schedule, side, total_lots)
        if not ok:
            log(f"[SCHEDULE-EXEC] Refus par RiskGuard: {reason}", self.logging_enabled)
            return False

        payload_market = self.order_builder.build_market_order(
            side=int(side),
            size=total_lots,
            account_id=int(self.config.account_id),
            contract_id=contract_id,
            order_type=int(getattr(self.config, "default_order_type", 2)),
        )

        log(f"[SCHEDULE-EXEC] Envoi MARKET (schedule={schedule.get('id','?')}, total_lots={total_lots})", self.logging_enabled)
        result = self.order_sender.send(payload_market, tag="MARKET")
        if not result["success"]:
            log(f"[SCHEDULE-EXEC] MARKET échec: {result}", self.logging_enabled)
            return False

        entry_order_id = result["order_id"]
        log(f"[SCHEDULE-EXEC] MARKET ok, orderId={entry_order_id}", self.logging_enabled)

        # TP partiel ou complet
        if tp_lots > 0:
            self.tp_placer.place_tp_after_entry(
                account_id=int(self.config.account_id),
                contract_id=contract_id,
                entry_order_id=entry_order_id,
                entry_side=side,
                size=tp_lots,
                override_ticks=override_ticks,
            )
        else:
            log("[SCHEDULE-EXEC] Aucun TP demandé (tp_lots=0).", self.logging_enabled)

        remaining = total_lots - tp_lots
        if remaining > 0:
            if carry_remaining:
                log(f"[SCHEDULE-EXEC] {remaining} lots restent ouverts (carry).", self.logging_enabled)
            else:
                log(f"[SCHEDULE-EXEC] {remaining} lots sans TP explicite (vérifie la stratégie A).", self.logging_enabled)

        return True
