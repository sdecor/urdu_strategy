# orders/order_sender.py
from __future__ import annotations
from typing import Dict, Any
from utils.logger import log


class OrderSender:
    """
    Envoie les ordres via un 'engine' qui expose place_order(payload) (Sim ou Live).
    Normalise la réponse pour l'executor.
    """

    def __init__(self, engine, logging_enabled: bool = True):
        self.engine = engine
        self.logging_enabled = logging_enabled

        if not hasattr(self.engine, "place_order"):
            raise ValueError("OrderSender: l'engine fourni n'expose pas 'place_order(payload)'.")

    def _get_first_present(self, obj: Dict[str, Any], *keys):
        for k in keys:
            if k in obj:
                return obj[k]
        return None

    def send(self, payload: Dict[str, Any], tag: str = "") -> Dict[str, Any]:
        """
        Envoie un ordre et retourne une réponse normalisée:
        {
          "success": bool,
          "order_id": int|None,
          "status": int|None,
          "error_code": int|None,
          "error_message": str|None,
          "raw": dict
        }
        """
        try:
            res = self.engine.place_order(payload) or {}
        except Exception as e:
            msg = f"OrderSender: exception engine.place_order -> {e}"
            log(f"[ORDER-SENDER] {msg}", self.logging_enabled)
            return {
                "success": False,
                "order_id": None,
                "status": None,
                "error_code": None,
                "error_message": msg,
                "raw": None,
            }

        success = bool(res.get("success", False))
        order_id = self._get_first_present(res, "orderId", "order_id")
        status = self._get_first_present(res, "status")
        # ⚠️ ne pas perdre 0 en utilisant 'or'
        error_code = self._get_first_present(res, "errorCode", "error_code")
        error_message = self._get_first_present(res, "errorMessage", "error_message")

        if tag:
            log(f"[ORDER-SENDER] {tag} -> success={success} order_id={order_id}", self.logging_enabled)
        return {
            "success": success,
            "order_id": order_id,
            "status": status,
            "error_code": error_code,
            "error_message": error_message,
            "raw": res,
        }
