from utils.logger import log
from api.mappings import map_position_to_side
from api.errors import assert_business_success, BusinessError


class OrdersService:
    def __init__(self, http_base, contract_id, default_order_type=2):
        self.http = http_base
        self.contract_id = contract_id
        self.default_order_type = int(default_order_type)

    def place_order(
        self,
        *,
        position: int,
        size: int = 1,
        order_type: int | None = None,
        limitPrice: float | None = None,
        stopPrice: float | None = None,
        trailPrice: float | None = None,
        customTag: str | None = None,
        linkedOrderId: int | None = None
    ):
        endpoint = self.http.endpoints.get("order_place")
        if not endpoint:
            log("[ERREUR] Endpoint 'order_place' manquant dans la configuration.", self.http.logging_enabled)
            return

        side = map_position_to_side(position)  # 0=buy, 1=sell
        if side is None:
            log(f"[ERREUR] Position invalide : {position}", self.http.logging_enabled)
            return

        _type = int(order_type) if order_type is not None else self.default_order_type

        payload = {
            "accountId": self.http.account_id,
            "contractId": self.contract_id,
            "type": _type,
            "side": side,
            "size": int(size),
        }
        if limitPrice is not None:
            payload["limitPrice"] = float(limitPrice)
        if stopPrice is not None:
            payload["stopPrice"] = float(stopPrice)
        if trailPrice is not None:
            payload["trailPrice"] = float(trailPrice)
        if customTag is not None:
            payload["customTag"] = str(customTag)
        if linkedOrderId is not None:
            payload["linkedOrderId"] = int(linkedOrderId)

        url = f"{self.http.base_url}{endpoint}"
        log(f"[TRADE] Commande préparée pour envoi :", self.http.logging_enabled)
        log(f"[TRADE] URL: {url}", self.http.logging_enabled)
        log(f"[TRADE] Headers: {dict(self.http.session.headers)}", self.http.logging_enabled)
        log(f"[TRADE] Payload: {payload}", self.http.logging_enabled)

        if not self.http.is_token_valid():
            log("[AUTH] Token invalide ou expiré.", self.http.logging_enabled)
            log("[TRADE] Abandon : token invalide, impossible d’envoyer l’ordre.", self.http.logging_enabled)
            return

        resp_json = self.http._post(endpoint, payload, tag="[TRADE]")
        try:
            assert_business_success(resp_json, "[TRADE]", self.http.logging_enabled)
        except BusinessError:
            return
        return resp_json

    def cancel_order(self, order_id: int):
        endpoint = self.http.endpoints.get("order_cancel")
        if not endpoint:
            log("[ERREUR] Endpoint 'order_cancel' manquant.", self.http.logging_enabled)
            return None
        payload = {"accountId": self.http.account_id, "orderId": int(order_id)}
        return self.http._post(endpoint, payload, tag="[CANCEL]")
