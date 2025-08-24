import datetime
from utils.logger import log

class TradeSimulator:
    def __init__(self, logging_enabled=True):
        self.trades = []
        self.logging_enabled = logging_enabled

    def execute_trade(self, instrument: str, position: int):
        trade = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "instrument": instrument,
            "position": position,
            "status": "simulated"
        }
        self.trades.append(trade)
        log(f"[SIMULATION] Trade simulé: {trade}", self.logging_enabled)

    def get_trade_log(self):
        return self.trades
