import requests

def get_open_positions(jwt_token, account_id, http):
    """
    Récupère les positions ouvertes via l'API TopstepX (/api/Position/searchOpen).
    """
    url = http.base_url.rstrip("/") + http.endpoints["position_search_open"]
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "accountId": account_id
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get("positions", [])
        else:
            print(f"[POSITION] ❌ Erreur HTTP {response.status_code}")
            print(f"[POSITION] Réponse : {response.text}")
    except Exception as e:
        print(f"[POSITION] ⚠️ Exception lors de l'appel à searchOpen : {e}")

    return []
