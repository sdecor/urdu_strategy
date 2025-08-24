from utils.logger import log


class AccountsService:
    """
    Service comptes/positions/ordres.
    """
    def __init__(self, http_base):
        self.http = http_base

    def get_open_positions(self):
        endpoint = self.http.endpoints.get("position_search_open")
        if not endpoint:
            log("[ERREUR] Endpoint 'position_search_open' manquant.", self.http.logging_enabled)
            return None
        payload = {"accountId": self.http.account_id}
        return self.http._post(endpoint, payload, tag="[POSITION]")

    def get_working_orders(self):
        endpoint = self.http.endpoints.get("order_search_open")
        if not endpoint:
            log("[ERREUR] Endpoint 'order_search_open' manquant.", self.http.logging_enabled)
            return None
        payload = {"accountId": self.http.account_id}
        return self.http._post(endpoint, payload, tag="[ORDERS]")
