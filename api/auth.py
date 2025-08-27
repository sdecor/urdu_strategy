# api/auth.py
import requests
from utils.logger import log
from utils.log_sanitizer import safe_log_api_call


class AuthAPI:
    """
    Wrapper minimal pour l'authentification /api/Auth/loginKey.
    """

    def __init__(self, base_url: str, endpoints: dict, logging_enabled: bool = True):
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
        self.logging_enabled = logging_enabled

    def login_key(self, payload: dict) -> dict:
        url = self.base_url + self.endpoints["login_key"]
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        safe_log_api_call("POST", url, headers, payload, log, self.logging_enabled, prefix="[AUTH]")
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            status = resp.status_code
            data = {}
            try:
                data = resp.json()
            except Exception:
                pass

            if status == 200 and data.get("success") and data.get("token"):
                log("[AUTH] Authentification réussie, token obtenu.", self.logging_enabled)
                return {"success": True, "status": status, "token": data.get("token"), "errorMessage": None}

            return {"success": False, "status": status, "token": None, "errorMessage": data.get("errorMessage") or resp.text}

        except requests.RequestException as e:
            return {"success": False, "status": 0, "token": None, "errorMessage": f"Network error: {e}"}
        except Exception as e:
            return {"success": False, "status": 0, "token": None, "errorMessage": f"Unexpected error: {e}"}
