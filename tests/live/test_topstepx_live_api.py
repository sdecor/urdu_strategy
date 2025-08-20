import os
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest
import requests
import yaml


def _load_settings() -> Dict[str, Any]:
    settings_path = os.environ.get("SETTINGS_PATH", str(Path("config") / "settings.yaml"))
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _headers(token: str) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _post(base_url: str, endpoints: Dict[str, str], name: str, payload: Dict[str, Any], token: str, timeout: int = 15) -> Tuple[int, Any, str]:
    url = f"{base_url.rstrip('/')}{endpoints.get(name, '')}"
    resp = requests.post(url, json=payload, headers=_headers(token), timeout=timeout)
    data = {}
    if resp.content:
        try:
            data = resp.json()
        except Exception:
            data = resp.text
    return resp.status_code, data, url


@pytest.fixture(scope="session")
def topstepx_cfg():
    s = _load_settings()
    ts = s.get("topstepx", {}) or {}
    base_url = str(ts.get("base_url") or "").strip()
    account_id = str(ts.get("account_id") or "").strip()
    endpoints = ts.get("endpoints", {}) or {}
    api_key_env = str((ts.get("auth", {}) or {}).get("api_key_env") or "TOPSTEPX_API_KEY")
    token = os.environ.get(api_key_env, "")

    if os.environ.get("LIVE_API_TESTS", "").lower() not in ("1", "true", "yes"):
        pytest.skip("LIVE_API_TESTS non activé (définir LIVE_API_TESTS=1 pour exécuter les tests API live).")

    if not base_url or not base_url.lower().startswith(("http://", "https://")):
        pytest.skip("topstepx.base_url invalide ou vide.")
    if not account_id:
        pytest.skip("topstepx.account_id manquant.")
    if not token:
        pytest.skip(f"Variable d'environnement {api_key_env} manquante (clé API).")

    return {"base_url": base_url, "account_id": account_id, "endpoints": endpoints, "token": token}


@pytest.mark.parametrize(
    "endpoint_name",
    [
        "account_search",         # safe read
        "position_search_open",   # safe read
        "order_search_open",      # safe read
        "contract_available",     # safe read (peut renvoyer vide selon compte)
    ],
)
def test_topstepx_read_endpoints_ok(topstepx_cfg, endpoint_name):
    base_url = topstepx_cfg["base_url"]
    account_id = topstepx_cfg["account_id"]
    endpoints = topstepx_cfg["endpoints"]
    token = topstepx_cfg["token"]

    if endpoint_name not in endpoints:
        pytest.skip(f"Endpoint '{endpoint_name}' absent de la config.")

    payload = {"accountId": account_id}
    code, data, url = _post(base_url, endpoints, endpoint_name, payload, token, timeout=20)

    assert code >= 200 and code < 300, f"HTTP {code} pour {url} ⇒ {data}"


def test_topstepx_minimal_sanity(topstepx_cfg):
    base_url = topstepx_cfg["base_url"]
    account_id = topstepx_cfg["account_id"]
    endpoints = topstepx_cfg["endpoints"]
    token = topstepx_cfg["token"]

    # Requêtes essentielles
    essential = ["account_search", "position_search_open"]
    missing = [e for e in essential if e not in endpoints]
    if missing:
        pytest.skip(f"Endpoints essentiels manquants: {missing}")

    for ep in essential:
        code, data, url = _post(base_url, endpoints, ep, {"accountId": account_id}, token, timeout=20)
        assert 200 <= code < 300, f"HTTP {code} pour {url} ⇒ {data}"
