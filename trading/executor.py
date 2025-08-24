from trading.simulator import TradeSimulator
from api.topstep_client import TopstepXClient
from utils.logger import log

class TradeExecutor:
    def __init__(self, config):
        self.mode = config.mode
        self.logging_enabled = config.logging_enabled

        if self.mode == "live":
            self.engine = TopstepXClient(
                api_key=config.api_key,
                base_url=config.base_url,
                username=config.username,
                account_id=config.account_id,
                endpoints=config.api_endpoints,
                logging_enabled=self.logging_enabled
            )
        elif self.mode == "simulation":
            self.engine = TradeSimulator(logging_enabled=self.logging_enabled)
        else:
            raise ValueError(f"Mode inconnu : {self.mode}")

    def process_signal(self, signal: dict):
        instrument = signal.get("instrument")
        position = signal.get("position")

        if instrument is None or position is None:
            log(f"[AVERTISSEMENT] Signal invalide ignoré: {signal}", self.logging_enabled)
            return

        log(f"[EXECUTOR] Traitement signal {instrument} -> position {position}", self.logging_enabled)
        self.engine.execute_trade(instrument, position)
