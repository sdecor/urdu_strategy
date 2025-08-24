from utils.logger import log


class OrdersService:
    """
    Service ordres : place/cancel.
    Dépend du HttpBase pour le transport (_post, token, config).
    """
    def __init__(self, http_base, contract_id, default_order_type=2):
        self.http = http_base
        self.contract_id = contract_id
        self.default_order_type = int(default_order_type)

    def place_order(
        self,
        *,
        position: int,
        size: int = 1,
        order_type: int | None = None,  # 1=Limit, 2=Market, 4=Stop, 5=TrailingStop, 6=JoinBid, 7=JoinAsk
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

        side = self._determine_side(position)  # 0=buy, 1=sell
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

        # Logs pré-envoi
        url = f"{self.http.base_url}{endpoint}"
        log(f"[TRADE] Commande préparée pour envoi :", self.http.logging_enabled)
        log(f"[TRADE] URL: {url}", self.http.logging_enabled)
        log(f"[TRADE] Headers: {dict(self.http.session.headers)}", self.http.logging_enabled)
        log(f"[TRADE] Payload: {payload}", self.http.logging_enabled)

        # Vérif token
        if not self.http.is_token_valid():
            log("[AUTH] Token invalide ou expiré.", self.http.logging_enabled)
            log("[TRADE] Abandon : token invalide, impossible d’envoyer l’ordre.", self.http.logging_enabled)
            return

        # Envoi puis gestion du succès 'métier'
        resp_json = self.http._post(endpoint, payload, tag="[TRADE]")
        if resp_json is None:
            return

        success = resp_json.get("success", True) if isinstance(resp_json, dict) else True
        if not success:
            err_code = resp_json.get("errorCode", "N/A")
            err_msg  = resp_json.get("errorMessage", "N/A")
            log(f"[TRADE] ERREUR MÉTIER: success=false, code={err_code}, message='{err_msg}'", self.http.logging_enabled)
            return

        log("[TRADE] Succès métier confirmé (success=true).", self.http.logging_enabled)
        return resp_json

    def cancel_order(self, order_id: int):
        endpoint = self.http.endpoints.get("order_cancel")
        if not endpoint:
            log("[ERREUR] Endpoint 'order_cancel' manquant.", self.http.logging_enabled)
            return None
        payload = {"accountId": self.http.account_id, "orderId": int(order_id)}
        return self.http._post(endpoint, payload, tag="[CANCEL]")

    @staticmethod
    def _determine_side(position: int):
        # mapping doc: 0 = Bid (buy), 1 = Ask (sell)
        if position == 1:
            return 0  # BUY
        if position == -1:
            return 1  # SELL
        return None
