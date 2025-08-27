# api/flatten.py
import requests
from utils.logger import log
from utils.log_sanitizer import safe_log_api_call
from api.positions import get_open_positions


class FlattenService:
    """
    Clôture toutes les positions ouvertes via /api/Position/closeContract.
    """
    def __init__(self, accounts_service, logging_enabled=True):
        self.accounts_service = accounts_service
        self.logging_enabled = logging_enabled
        self.http = accounts_service.http

    def flatten_all(self):
        close_url = self.http.base_url.rstrip("/") + self.http.endpoints["position_close_contract"]
        jwt_token = self.http.jwt_token
        account_id = self.http.account_id

        log("[FLATTEN] Tentative de clôture via /Position/closeContract...", self.logging_enabled)

        open_positions = get_open_positions(jwt_token, account_id, self.http)
        if not open_positions:
            log("[FLATTEN] Aucune position ouverte détectée.", self.logging_enabled)
            return

        for pos in open_positions:
            contract_id = pos.get("contractId")
            if not contract_id:
                log("[FLATTEN] ❌ Contrat ID manquant, impossible de clôturer.", self.logging_enabled)
                continue

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            payload = {"accountId": account_id, "contractId": contract_id}

            safe_log_api_call("POST", close_url, headers, payload, log, self.logging_enabled, prefix="[FLATTEN]")
            try:
                response = requests.post(close_url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    log(f"✅ Clôture réussie pour le contrat {contract_id}", self.logging_enabled)
                else:
                    log(f"❌ Échec clôture contrat {contract_id} - HTTP {response.status_code}", self.logging_enabled)
                    try:
                        error = response.json().get("errorMessage", response.text)
                        log(f"   Message: {error}", self.logging_enabled)
                    except Exception:
                        log(f"   Réponse brute: {response.text}", self.logging_enabled)
            except Exception as e:
                log(f"⚠️ Erreur lors de l'appel à /closeContract : {e}", self.logging_enabled)
