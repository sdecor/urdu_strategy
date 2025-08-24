from datetime import datetime
from utils.logger import log


class TradeSimulator:
    """
    Simule les ordres comme si on envoyait à l’API TopstepX.
    Garde la même interface que TopstepXClient : execute_trade(instrument, position, size), flatten_all().
    """
    def __init__(self, logging_enabled=True):
        self.logging_enabled = logging_enabled

    def execute_trade(self, instrument: str, position: int, size: int = 1):
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "instrument": instrument,
            "position": position,
            "size": size,
            "status": "simulated"
        }
        log(f"[SIMULATION] Trade simulé: {event}", self.logging_enabled)
        return event

    def flatten_all(self):
        log("[SIMULATION] Flatten all simulé (aucune API réelle appelée).", self.logging_enabled)
        return {"simulated": True, "action": "flatten_all"}
