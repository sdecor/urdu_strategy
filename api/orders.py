# api/orders.py
import requests
from utils.logger import log
from utils.log_sanitizer import safe_log_api_call


class OrdersAPI:
    """
    Wrapper pour les endpoints liés aux ordres :
    - place_order()
    - cancel_order()
    - search_orders()
    - search_open_orders()
    """

    def __init__(self, config, http_client):
        self.config = config
        self.http = http_client
        self.base_url = http_client.base_url.rstrip("/")
        self.endpoints = config.api_endpoints

    def place_order(self, payload: dict) -> dict:
        url = self.base_url + self.endpoints["order_place"]
        headers = {
            "Authorization": f"Bearer {self.http.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        safe_log_api_call("POST", url, headers, payload, log, self.config.logging_enabled, prefix="[ORDER]")

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            data = resp.json() if resp.status_code == 200 else {}
            return {
                "status": resp.status_code,
                "success": data.get("success", False),
                "orderId": data.get("orderId"),
                "errorCode": data.get("errorCode"),
                "errorMessage": data.get("errorMessage") or resp.text,
            }
        except Exception as e:
            return {"success": False, "errorMessage": str(e)}

    def cancel_order(self, order_id: int) -> dict:
        url = self.base_url + self.endpoints["order_cancel"]
        headers = {
            "Authorization": f"Bearer {self.http.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"accountId": int(self.config.account_id), "orderId": order_id}
        safe_log_api_call("POST", url, headers, payload, log, self.config.logging_enabled, prefix="[ORDER-CANCEL]")

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            data = resp.json() if resp.status_code == 200 else {}
            return {
                "status": resp.status_code,
                "success": data.get("success", resp.status_code in (200, 204)),
                "errorCode": data.get("errorCode"),
                "errorMessage": data.get("errorMessage") or resp.text,
            }
        except Exception as e:
            return {"success": False, "errorMessage": str(e)}

    def search_orders(self, criteria: dict) -> dict:
        url = self.base_url + self.endpoints["order_search"]
        headers = {
            "Authorization": f"Bearer {self.http.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        safe_log_api_call("POST", url, headers, criteria, log, self.config.logging_enabled, prefix="[ORDER-SEARCH]")

        try:
            resp = requests.post(url, headers=headers, json=criteria, timeout=10)
            return resp.json() if resp.status_code == 200 else {"status": resp.status_code, "text": resp.text}
        except Exception as e:
            return {"success": False, "errorMessage": str(e)}

    def search_open_orders(self) -> dict:
        url = self.base_url + self.endpoints["order_search_open"]
        headers = {
            "Authorization": f"Bearer {self.http.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"accountId": int(self.config.account_id)}
        safe_log_api_call("POST", url, headers, payload, log, self.config.logging_enabled, prefix="[ORDER-OPEN]")

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json() if resp.status_code == 200 else {"status": resp.status_code, "text": resp.text}
        except Exception as e:
            return {"success": False, "errorMessage": str(e)}
