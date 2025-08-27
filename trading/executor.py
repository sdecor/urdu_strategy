# trading/executor.py
from __future__ import annotations

from typing import Optional, Dict, Any

from utils.logger import log
from trading.simulator import TradeSimulator
from api.topstep_client import TopstepXClient
from orders.order_builder import OrderBuilder
from orders.order_sender import OrderSender
from fills.fill_resolver import FillResolver
from strategy.tp_manager import TPManager
from strategy.tp_placer import TPPlacer
from strategy.schedule_executor import ScheduleExecutor
from risk.risk_guard import RiskGuard

class TradeExecutor:
    """
    Orchestration des ordres (live/simu) + pose TP.
    Modularisation:
      - Construction payloads => OrderBuilder
      - Envoi => OrderSender
      - Récupération fill => FillResolver
      - Pose TP => TPPlacer
      - Exécution de schedule (A/B) => ScheduleExecutor
    """

    def __init__(self, config, mode: Optional[str] = None, logging_enabled: Optional[bool] = None):
        self.config = config
        self.mode = mode or getattr(config, "mode", "simulation")
        self.logging_enabled = logging_enabled if logging_enabled is not None else getattr(config, "logging_enabled", True)

        # Engines
        if self.mode == "live":
            self.engine = TopstepXClient(config)
        else:
            self.engine = TradeSimulator(config)

        # Services
        self.order_builder = OrderBuilder(config)
        self.order_sender = OrderSender(self.engine, logging_enabled=self.logging_enabled)
        self.fill_resolver = FillResolver(self.engine, config, logging_enabled=self.logging_enabled)
        self.tp_manager = TPManager(config, logging_enabled=self.logging_enabled)
        self.tp_placer = TPPlacer(self.tp_manager, self.fill_resolver, self.order_sender, logging_enabled=self.logging_enabled)
        self.schedule_executor = ScheduleExecutor(
            config=config,
            order_builder=self.order_builder,
            order_sender=self.order_sender,
            tp_placer=self.tp_placer,
            risk_guard=RiskGuard(config, logging_enabled=self.logging_enabled),  # 👈 injection
            logging_enabled=self.logging_enabled
        )

    # --- Helpers ---
    def get_default_quantity(self) -> int:
        return int(getattr(self.config, "default_quantity", 1))

    def get_default_order_type(self) -> int:
        return int(getattr(self.config, "default_order_type", 2))

    # --- API publique ---
    def flatten_all(self, instrument: str) -> None:
        if hasattr(self.engine, "flatten_all"):
            self.engine.flatten_all()
        else:
            log("[EXECUTOR] flatten_all non supporté par le moteur courant.", self.logging_enabled)

    def place_market(self, instrument: str, side: int, size: Optional[int] = None) -> bool:
        """
        Compat héritée: place un MARKET puis TP sur 'size' (tout), en utilisant la config globale.
        (Déjà modularisé via Builder/Sender/TPPlacer)
        """
        contract_id = getattr(self.config, "contract_id", None)
        if not contract_id:
            log("[EXECUTOR] contract_id manquant dans config.", self.logging_enabled)
            return False

        size = int(size or self.get_default_quantity())
        payload = self.order_builder.build_market_order(
            side=int(side),
            size=size,
            account_id=int(self.config.account_id),
            contract_id=contract_id,
            order_type=self.get_default_order_type(),
        )

        log("[EXECUTOR] Envoi MARKET", self.logging_enabled)
        result = self.order_sender.send(payload, tag="MARKET")
        if not result["success"]:
            log(f"[EXECUTOR] MARKET échec: {result}", self.logging_enabled)
            return False

        order_id = result["order_id"]
        log(f"[EXECUTOR] MARKET ok, orderId={order_id}", self.logging_enabled)

        # Pose TP (global)
        self.tp_placer.place_tp_after_entry(
            account_id=int(self.config.account_id),
            contract_id=contract_id,
            entry_order_id=order_id,
            entry_side=side,
            size=size,
        )
        return True

    def place_market_with_schedule(self, schedule: Dict[str, Any], side: int) -> bool:
        """
        API publique conservée pour compatibilité avec TradeRulesEngine.
        Délègue entièrement au ScheduleExecutor.
        """
        return self.schedule_executor.execute(schedule, side)
