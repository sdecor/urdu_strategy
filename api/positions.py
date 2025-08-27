# api/positions.py
import requests
from utils.logger import log
from utils.log_sanitizer import safe_log_api_call


def get_open_positions(jwt_token: str, account_id: int, http) -> list:
    """
    Récupère les positions ouvertes via l'API TopstepX (/api/Position/searchOpen).
    """
    url = http.base_url.rstrip("/") + http.endpoints["position_search_open"]
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"accountId": int(account_id)}

    safe_log_api_call("POST", url, headers, payload, log, True, prefix="[POSITION]")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            positions = data.get("positions", [])
            return positions if isinstance(positions, list) else []
        else:
            log(f"[POSITION] ❌ HTTP {response.status_code}", True)
            log(f"[POSITION] Réponse : {response.text}", True)
    except Exception as e:
        log(f"[POSITION] ⚠️ Exception lors de l'appel à searchOpen : {e}", True)

    return []
