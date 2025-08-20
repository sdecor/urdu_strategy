import os
from typing import Any, Dict, Optional, Tuple
import requests
import yaml
from pathlib import Path


class TopstepXClient:
    def __init__(self, settings_path: Optional[str] = None, session: Optional[requests.Session] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self._settings_path = settings_path or os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
        with open(self._settings_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f) or {}
        ts = self._settings.get("topstepx", {}) or {}
        self._base_url = ts.get("base_url", "").rstrip("/")
        self._account_id = ts.get("account_id") or ""
        self._endpoints = ts.get("endpoints", {}) or {}
        self._api_key = os.environ.get(ts.get("auth", {}).get("api_key_env", "TOPSTEPX_API_KEY"), "")
        self._session = session or requests.Session()

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    def _url(self, name: str) -> str:
        ep = self._endpoints.get(name, "")
        return f"{self._base_url}{ep}"

    def place_order(self, instrument: str, side: str, qty: int, order_type: str = "MARKET", client_tag: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        payload = {
            "accountId": self._account_id,
            "instrument": instrument,
            "side": side,
            "qty": int(qty),
            "type": order_type,
            "clientTag": client_tag,
        }
        try:
            resp = self._session.post(self._url("order_place"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def cancel_order(self, order_id: str) -> Tuple[bool, Dict[str, Any]]:
        payload = {"accountId": self._account_id, "orderId": order_id}
        try:
            resp = self._session.post(self._url("order_cancel"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def search_open_orders(self) -> Tuple[bool, Dict[str, Any]]:
        payload = {"accountId": self._account_id}
        try:
            resp = self._session.post(self._url("order_search_open"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def search_open_positions(self) -> Tuple[bool, Dict[str, Any]]:
        payload = {"accountId": self._account_id}
        try:
            resp = self._session.post(self._url("position_search_open"), json=payload, headers=self._headers(), timeout=30)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.content else {}
            return ok, data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return False, {"error": str(e)}

    def flat_position(self, instrument: str, qty: int, side_to_close: str, client_tag: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        side = "SELL" if side_to_close.upper() == "LONG" else "BUY"
        return self.place_order(instrument=instrument, side=side, qty=qty, order_type="MARKET", client_tag=client_tag)
