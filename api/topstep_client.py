import requests
from datetime import datetime
from utils.logger import log

class TopstepXClient:
    def __init__(self, api_key, base_url, username, account_id, endpoints=None, logging_enabled=True):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.account_id = account_id
        self.endpoints = endpoints or {}
        self.logging_enabled = logging_enabled

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def execute_trade(self, instrument: str, position: int):
        endpoint = self.endpoints.get("order_place")
        if not endpoint:
            log("[ERREUR] Endpoint 'order_place' manquant dans la configuration.", self.logging_enabled)
            return

        url = f"{self.base_url}{endpoint}"
        payload = {
            "account_id": self.account_id,
            "username": self.username,
            "instrument": instrument,
            "position": position,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            log(f"[TRADE] Ordre envoyé avec succès : {payload}", self.logging_enabled)
            log(f"[TRADE] Réponse API : {response.status_code} - {response.text}", self.logging_enabled)
        except requests.RequestException as e:
            log(f"[ERREUR] Envoi d’ordre échoué : {e}", self.logging_enabled)
