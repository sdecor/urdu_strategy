import requests
from utils.logger import log


class HttpBase:
    """
    Socle HTTP : authentification, session, _post, vérification de token.
    Ne connaît pas la logique d'ordres/positions — seulement le transport.
    """
    def __init__(self, api_key, base_url, username, account_id, endpoints, logging_enabled=True):
        self.api_key = api_key                  # clé fixe pour /Auth/loginKey
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.account_id = int(account_id)
        self.endpoints = endpoints or {}
        self.logging_enabled = logging_enabled

        # 1) Auth : obtenir le token d'accès via /Auth/loginKey
        self.jwt_token = self._authenticate()

        # 2) Session HTTP avec Bearer token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    # ---------- Auth ----------
    def _authenticate(self) -> str:
        endpoint = self.endpoints.get("login_key")
        if not endpoint:
            log("[AUTH] Endpoint 'login_key' manquant dans la configuration.", self.logging_enabled)
            return ""
        url = f"{self.base_url}{endpoint}"
        payload = {"userName": self.username, "apiKey": self.api_key}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            log(f"[AUTH] POST {url} -> {resp.status_code}", self.logging_enabled)
            log(f"[AUTH] Réponse brute: {resp.text}", self.logging_enabled)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    token = data.get("token")
                    if token:
                        log("[AUTH] Authentification réussie, token obtenu.", self.logging_enabled)
                        return token
                    log("[AUTH] Aucune clé 'token' dans la réponse JSON.", self.logging_enabled)
                except Exception as e:
                    log(f"[AUTH] ERREUR lors du décodage JSON: {e}", self.logging_enabled)
            else:
                log(f"[AUTH] Échec d'authentification : HTTP {resp.status_code}", self.logging_enabled)
                log(f"[AUTH] Message : {resp.text}", self.logging_enabled)
        except requests.RequestException as e:
            log(f"[AUTH] Erreur réseau lors de l'authentification : {e}", self.logging_enabled)
        return ""

    def is_token_valid(self) -> bool:
        endpoint = self.endpoints.get("account_search")
        if not endpoint:
            log("[AUTH] Endpoint 'account_search' manquant pour validation token.", self.logging_enabled)
            return False
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.post(url, json={})
            log(f"[AUTH] Vérif token -> {resp.status_code}", self.logging_enabled)
            if resp.status_code == 200:
                return True
            if resp.status_code == 401:
                return False
            log(f"[AUTH] Réponse inattendue lors de la vérif token: {resp.status_code} | {resp.text}", self.logging_enabled)
            return False
        except requests.RequestException as e:
            log(f"[AUTH] ERREUR lors de la vérification du token : {e}", self.logging_enabled)
            return False

    # ---------- Transport ----------
    def _post(self, endpoint: str, payload: dict, tag="[API]"):
        url = f"{self.base_url}{endpoint}"
        log(f"{tag} Envoi POST => URL: {url}", self.logging_enabled)
        log(f"{tag} Headers: {dict(self.session.headers)}", self.logging_enabled)
        log(f"{tag} Payload: {payload}", self.logging_enabled)
        try:
            response = self.session.post(url, json=payload)
            log(f"{tag} Statut HTTP: {response.status_code}", self.logging_enabled)
            log(f"{tag} Réponse brute: {response.text}", self.logging_enabled)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return {"raw": response.text}
        except requests.HTTPError as e:
            log(f"{tag} ERREUR HTTP: {e}", self.logging_enabled)
        except requests.RequestException as e:
            log(f"{tag} ERREUR réseau: {e}", self.logging_enabled)
        return None
