from trading.simulator import TradeSimulator
from api.topstep_client import TopstepXClient
from utils.logger import log
from utils.state import STATE


class TradeExecutor:
    def __init__(self, config):
        self.mode = config.mode
        self.config = config
        self.logging_enabled = config.logging_enabled

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
        - position == 1  -> BUY (market)
        - position == -1 -> SELL (market)
        - position == 0  -> FLATTEN (fermeture de toutes les positions du contrat configuré)
        """
        instrument = signal.get("instrument")
        position = signal.get("position")

        if instrument is None or position is None:
            log(f"[AVERTISSEMENT] Signal invalide ignoré: {signal}", self.logging_enabled)
            return

        if position == 0:
            log("[EXECUTOR] Flatten all demandé", self.logging_enabled)
            result = self.flatten_all(instrument)
            STATE.record_trade_event(instrument, 0, 0, {"flatten": True, "result": result})
            return

        size = self.config.default_quantity  # gestion des lots par l'app
        log(f"[EXECUTOR] Traitement signal {instrument} -> position {position} (qty={size})", self.logging_enabled)
        result = self.engine.execute_trade(instrument, position, size)
        STATE.record_trade_event(instrument, position, size, result)

    def flatten_all(self, instrument: str):
        """
        Demande au moteur de fermer toutes les positions du contrat configuré.
        """
        if hasattr(self.engine, "flatten_all"):
            return self.engine.flatten_all()
        log("[EXECUTOR] flatten_all non supporté par le moteur courant.", self.logging_enabled)
        return None
