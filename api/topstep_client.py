# api/topstep_client.py
from __future__ import annotations

from typing import Optional, Dict, Any

from api.http_base import HttpBase
from api.orders import OrdersAPI
from api.flatten import FlattenService
from api.positions import get_open_positions


class TopstepXClient:
    """
    Client haut niveau pour l'exécution LIVE :
    - Auth + HTTP via HttpBase
    - place_order(payload)
    - get_open_positions()
    - flatten_all()
    """

    def __init__(self, config, logging_enabled: Optional[bool] = None):
        self.config = config
        self.logging_enabled = logging_enabled if logging_enabled is not None else getattr(config, "logging_enabled", True)

        self.http = HttpBase(config, logging_enabled=self.logging_enabled)
        self.orders = OrdersAPI(config, self.http)
        self.flatten_service = FlattenService(accounts_service=self, logging_enabled=self.logging_enabled)

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.orders.place_order(payload)

    def get_open_positions(self) -> list:
        return get_open_positions(self.http.jwt_token, self.http.account_id, self.http)

    def flatten_all(self) -> None:
        self.flatten_service.flatten_all()
