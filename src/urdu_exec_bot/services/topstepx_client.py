import os
from typing import Any, Dict, Optional, Tuple, Union
import requests
import yaml
from pathlib import Path
from enum import Enum


class TSOrderType(int, Enum):
    LIMIT = 1
    MARKET = 2
    STOP = 4
    TRAILING_STOP = 5
    JOIN_BID = 6
    JOIN_ASK = 7


class TSSide(int, Enum):
    BUY = 0   # Bid
    SELL = 1  # Ask


class TopstepXClient:
    """
    Client ProjectX/TopstepX :
    - Auth via /api/Auth/loginKey avec (username, apiKey) -> session token (JWT)
    - Ensuite Authorization: Bearer <token> pour tous les appels
    - Champs ProjectX (type/side/size/customTag)
    """

    def __init__(self, settings_path: Optional[str] = None, session: Optional[requests.Session] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self._settings_path = settings_path or os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
        with open(self._settings_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f) or {}

        ts = self._settings.get("topstepx", {}) or {}
        self._base_url = (ts.get("base_url") or "").rstrip("/")
        self._account_id = str(ts.get("account_id") or "").strip()
        self._username = str(ts.get("username") or "").strip()
        self._endpoints = ts.get("endpoints", {}) or {}
        self._contracts = {str(k).upper(): str(v) for k, v in (ts.get("contracts") or {}).items()}

        api_key_env = (ts.get("auth", {}) or {}).get("api_key_env") or "TOPSTEPX_API_KEY"
        self._api_key = os.environ.get(api_key_env, "")
        self._session = session or requests.Session()
        self._token: Optional[str] = None

    # ----------------------------- utils -----------------------------

    def _url(self, name: str) -> str:
        ep = self._endpoints.get(name, "")
        return f"{self._base_url}{ep}"

    def _headers(self, use_bearer: bool = True) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if use_bearer and self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def resolve_contract_id(self, instrument: str) -> Optional[str]:
        if not instrument:
            return None
        return self._contracts.get(str(instrument).upper())

    @staticmethod
    def _map_type(order_type: Union[str, TSOrderType]) -> int:
        if isinstance(order_type, TSOrderType):
            return int(order_type.value)
        s = str(order_type).upper()
        return {
            "LIMIT": int(TSOrderType.LIMIT),
            "MARKET": int(TSOrderType.MARKET),
            "STOP": int(TSOrderType.STOP),
            "TRAILING_STOP": int(TSOrderType.TRAILING_STOP),
            "JOIN_BID": int(TSOrderType.JOIN_BID),
            "JOIN_ASK": int(TSOrderType.JOIN_ASK),
        }.get(s, int(TSOrderType.MARKET))

    @staticmethod
    def _map_side(side: Union[str, TSSide]) -> int:
        if isinstance(side, TSSide):
            return int(side.value)
        s = str(side).upper()
        if s in ("BUY", "BID", "0"):
            return int(TSSide.BUY)
        if s in ("SELL", "ASK", "1"):
            return int(TSSide.SELL)
        return int(TSSide.BUY)

    # --------------------------- auth flows --------------------------

    def login_with_key(self, timeout: int = 20) -> Tuple[bool, Dict[str, Any]]:
        """
        POST /api/Auth/loginKey { userName, apiKey } -> { token, success, ... }
        """
        if not self._username or not self._api_key:
            return False, {"error": "missing username or apiKey"}
        url = self._url("login_key") or f"{self._base_url}/api/Auth/loginKey"
        payload = {"userName": self._username, "apiKey": self._api_key}
        try:
            resp = self._session.post(url, json=payload, headers=self._headers(use_bearer=False), timeout=timeout)
            data = resp.json() if resp.content else {}
            ok = 200 <= resp.status_code < 300 and bool(data.get("success", False)) and data.get("token")
            if ok:
                self._token = str(data["token"])
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def validate_token(self, timeout: int = 10) -> Tuple[bool, Dict[str, Any]]:
        url = self._url("validate_token") or f"{self._base_url}/api/Auth/validate"
        try:
            resp = self._session.post(url, json={}, headers=self._headers(), timeout=timeout)
            data = resp.json() if resp.content else {}
            ok = 200 <= resp.status_code < 300
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def _ensure_auth(self) -> None:
        if not self._token:
            ok, _ = self.login_with_key()
            if not ok:
                raise RuntimeError("TopstepX loginKey failed")

    # ---------------------------- endpoints --------------------------

    def place_order(
        self,
        instrument: str,
        side: Union[str, TSSide],
        qty: int,
        order_type: Union[str, TSOrderType] = "MARKET",
        client_tag: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        self._ensure_auth()
        payload = {
            "accountId": int(self._account_id) if str(self._account_id).isdigit() else self._account_id,
            "contractId": self.resolve_contract_id(instrument),
            "type": self._map_type(order_type),   # ProjectX: type
            "side": self._map_side(side),         # ProjectX: side
            "size": int(qty),                     # ProjectX: size
            "customTag": client_tag,
            "username": self._username or None,
        }
        if extra:
            payload.update(extra)
        try:
            resp = self._session.post(self._url("order_place"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def cancel_order(self, order_id: Union[str, int]) -> Tuple[bool, Dict[str, Any]]:
        self._ensure_auth()
        payload = {"accountId": self._account_id, "orderId": order_id, "username": self._username or None}
        try:
            resp = self._session.post(self._url("order_cancel"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def search_open_orders(self) -> Tuple[bool, Dict[str, Any]]:
        self._ensure_auth()
        payload = {"accountId": self._account_id, "username": self._username or None}
        try:
            resp = self._session.post(self._url("order_search_open"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def search_open_positions(self) -> Tuple[bool, Dict[str, Any]]:
        self._ensure_auth()
        payload = {"accountId": self._account_id, "username": self._username or None}
        try:
            resp = self._session.post(self._url("position_search_open"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def account_search(self) -> Tuple[bool, Dict[str, Any]]:
        self._ensure_auth()
        # ProjectX recommande onlyActiveAccounts
        payload = {"onlyActiveAccounts": True}
        try:
            resp = self._session.post(self._url("account_search"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def contract_available(self) -> Tuple[bool, Dict[str, Any]]:
        self._ensure_auth()
        payload = {"live": True}
        try:
            resp = self._session.post(self._url("contract_available"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def flat_position(self, instrument: str, qty: int, side_to_close: str, client_tag: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        side = TSSide.SELL if str(side_to_close).upper() == "LONG" else TSSide.BUY
        return self.place_order(instrument=instrument, side=side, qty=qty, order_type=TSOrderType.MARKET, client_tag=client_tag)
