from trading.simulator import TradeSimulator
from api.topstep_client import TopstepXClient
from utils.logger import log
from trading.lot_manager import LotManager

class TradeExecutor:
    def __init__(self, config):
        self.mode = config.mode
        self.config = config  # pour accéder à default_quantity
        self.logging_enabled = config.logging_enabled
        self.lot_manager = LotManager(
            default_quantity=config.default_quantity,
            logging_enabled=config.logging_enabled
        )
        
        if self.mode == "live":
            self.engine = TopstepXClient(
                api_key=config.api_key,
                base_url=config.base_url,
                username=config.username,
                account_id=config.account_id,
                endpoints=config.api_endpoints,
                contract_id=config.contract_id,
                logging_enabled=self.logging_enabled,
                default_order_type=getattr(config, "default_order_type", 2)
            )

        elif self.mode == "simulation":
            self.engine = TradeSimulator(logging_enabled=self.logging_enabled)
        else:
            raise ValueError(f"Mode inconnu : {self.mode}")

    def process_signal(self, signal: dict):
        """
        Traite un signal selon le mode défini.
        La quantité (lots) est gérée par l'application, jamais par le signal.
        """
        instrument = signal.get("instrument")
        position = signal.get("position")
        quantity = self.lot_manager.get_quantity(instrument, signal)

        if instrument is None or position is None:
            log(f"[AVERTISSEMENT] Signal invalide ignoré: {signal}", self.logging_enabled)
            return

        log(f"[EXECUTOR] Traitement signal {instrument} -> position {position} (qty={quantity})", self.logging_enabled)
        self.engine.execute_trade(instrument, position, quantity)

