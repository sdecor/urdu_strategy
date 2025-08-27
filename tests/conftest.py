# tests/conftest.py
import os
import sys
import pytest

# --- 1) Assure l'import des packages du projet (ajoute la racine au sys.path) ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from types import SimpleNamespace

CONTRACT_ID = "CON.F.US.ULA.U25"


class DummyConfig:
    """
    Config minimale pour tests, sans accès au YAML/.env.
    """
    def __init__(self):
        # Sensibles (mock)
        self.api_key = "TEST_KEY"
        self.base_url = "https://api.topstepx.com"
        self.username = "tester"
        self.account_id = 123456

        # Mode / logs
        self.mode = "simulation"
        self.logging_enabled = False

        # Trading/strategy
        self.default_order_type = 2
        self.default_quantity = 1
        self.contract_id = CONTRACT_ID
        self.strategy = {
            "tp": {
                "ticks": 4,                # fallback global de ticks pour TPManager
                "default_quantity": 1
            }
        }
        self.contracts = {
            CONTRACT_ID: {
                "tick_size": "1/32"        # 0.03125
            }
        }

        # Config brute (pour FillResolver config.fills)
        self.config = {
            "fills": {
                "retries": 3,
                "delay_seconds": 0.01,
                "jitter_seconds": 0.0,
                "require_size_nonzero": True,
                "source": "positions",
            },
            # Optionnel: risk
            # "risk": {"max_order_size": 10, "min_minutes_before_stop": 5}
        }

        # Non utilisés ici, mais présents dans le projet
        self.paths = {}
        self.dashboard = {}
        self.api_endpoints = {}
        self.trading_hours = {"start_utc": "00:00", "stop_utc": "23:59"}
        self.strategy_templates = []
        self.schedules = []


@pytest.fixture
def config():
    return DummyConfig()


@pytest.fixture
def simulator_spy(monkeypatch):
    """
    Patch le TradeSimulator pour:
      - collecter tous les payloads passés à place_order
      - retourner un succès avec orderId croissant
      - get_open_positions renvoie un fill pour le contrat testé
    """
    from trading import simulator

    calls = []

    counter = {"oid": 1500000000}

    def fake_place_order(self, payload):
        # stocke pour assertions
        calls.append(("place_order", dict(payload)))
        # réponse simulée
        counter["oid"] += 1
        return {"success": True, "orderId": counter["oid"], "errorCode": 0, "errorMessage": None}

    def fake_get_open_positions(self):
        # prix moyen / fill présent immédiatement
        return [{"contractId": CONTRACT_ID, "size": 1, "averagePrice": 117.0}]

    monkeypatch.setattr(simulator.TradeSimulator, "place_order", fake_place_order, raising=True)
    monkeypatch.setattr(simulator.TradeSimulator, "get_open_positions", fake_get_open_positions, raising=True)

    return calls
