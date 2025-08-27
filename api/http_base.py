# api/http_base.py
from __future__ import annotations

import requests
from typing import Optional

from utils.logger import log
from utils.log_sanitizer import safe_log_api_call
from api.auth import AuthAPI


class HttpBase:
    """
    Base HTTP pour l'API TopstepX :
    - Gère l'authentification via /api/Auth/loginKey
    - Expose base_url, endpoints, account_id, jwt_token
    - Centralise les headers 'Bearer …token…' (non loggé en clair)
    """

    def __init__(self, config, logging_enabled: bool = True):
        self.config = config
        self.logging_enabled = logging_enabled

        self.base_url: str = (getattr(config, "base_url", "") or "").rstrip("/")
        self.endpoints: dict = getattr(config, "api_endpoints", {}) or {}
        self.account_id: int = int(getattr(config, "account_id", 0)) if getattr(config, "account_id", None) else 0

        if not self.base_url:
            raise ValueError("HttpBase: base_url manquant (vérifie .env TOPSTEPX_BASE_URL)")
        if "login_key" not in self.endpoints:
            raise ValueError("HttpBase: endpoint 'login_key' manquant dans config.api_endpoints.")

        self.jwt_token: str = self._authenticate()

    # -------- Auth --------
    def _authenticate(self) -> str:
        username = getattr(self.config, "username", None)
        api_key = getattr(self.config, "api_key", None)
        if not username or not api_key:
            raise ValueError("HttpBase: username/api_key manquants (.env: TOPSTEPX_USERNAME / TOPSTEPX_API_KEY)")

        auth = AuthAPI(self.base_url, self.endpoints, logging_enabled=self.logging_enabled)
        payload = {"username": username, "apiKey": api_key}

        result = auth.login_key(payload)
        if not result.get("success"):
            raise RuntimeError(f"HttpBase: échec auth loginKey -> {result.get('errorMessage')}")
        token = result.get("token")
        if not token:
            raise RuntimeError("HttpBase: token absent dans la réponse d'authentification.")
        return token

    def refresh_token(self) -> None:
        self.jwt_token = self._authenticate()

    # -------- Helpers --------
    def build_headers(self, extra: Optional[dict] = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def safe_log_request(self, method: str, url: str, headers: dict, payload: dict | None = None, prefix: str = ""):
        safe_log_api_call(method, url, headers, payload or {}, log, self.logging_enabled, prefix=prefix)

    # -------- Low-level call --------
    def post_json(self, endpoint_key: str, payload: dict, timeout: int = 15, log_prefix: str = "") -> requests.Response:
        if endpoint_key not in self.endpoints:
            raise KeyError(f"HttpBase.post_json: endpoint inconnu '{endpoint_key}'")
        url = self.base_url + self.endpoints[endpoint_key]
        headers = self.build_headers()

        self.safe_log_request("POST", url, headers, payload, prefix=log_prefix)
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        return resp
