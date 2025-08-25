import requests
from utils.logger import log
from api.positions import get_open_positions

class FlattenService:
    def __init__(self, accounts_service, orders_service=None, contract_id=None, logging_enabled=True):
        self.accounts_service = accounts_service
        self.contract_id = contract_id
        self.logging_enabled = logging_enabled
        self.http = accounts_service.http  # Accès au HttpBase depuis accounts_service

    def flatten_all(self):
        """
        Clôture toutes les positions ouvertes via /Position/closeContract.
        """
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

            payload = {
                "accountId": account_id,
                "contractId": contract_id
            }

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            try:
                response = requests.post(close_url, headers=headers, json=payload)
                if response.status_code == 200:
                    log(f"✅ Clôture réussie pour le contrat {contract_id}", self.logging_enabled)
                else:
                    log(f"❌ Échec clôture contrat {contract_id} - Statut HTTP: {response.status_code}", self.logging_enabled)
                    try:
                        error = response.json().get("errorMessage", response.text)
                        log(f"   Message: {error}", self.logging_enabled)
                    except Exception:
                        log(f"   Réponse brute: {response.text}", self.logging_enabled)
            except Exception as e:
                log(f"⚠️ Erreur lors de l'appel à /closeContract : {e}", self.logging_enabled)
