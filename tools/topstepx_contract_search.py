# tools/topstepx_contract_search.py
import json
import os
import sys
import argparse
import requests

# Permet d'importer utils/ et api/ depuis tools/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.config_loader import Config
from api.http_base import HttpBase
from utils.logger import log


def ensure_dir_exists(file_path: str):
    directory = os.path.dirname(os.path.abspath(file_path))
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def search_contracts(search_text: str, live: bool, http: HttpBase) -> dict:
    """
    Appelle l'endpoint TopstepX /api/Contract/search pour rechercher des contrats.
    """
    url = http.base_url.rstrip("/") + http.endpoints["contract_search"]
    headers = {
        "Authorization": f"Bearer {http.jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "searchText": search_text,
        "live": live,
    }

    log(f"[CONTRACT] POST {url} | payload={payload}", True)
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
    except requests.RequestException as e:
        return {"success": False, "error": f"Network error: {e}"}

    if resp.status_code != 200:
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        return {"success": False, "status": resp.status_code, "response": data}

    try:
        data = resp.json()
    except Exception:
        return {"success": False, "error": "Invalid JSON in response", "raw": resp.text}

    if isinstance(data, dict) and "contracts" in data:
        return {"success": True, "contracts": data["contracts"], "raw": data}
    return {"success": True, "contracts": data if isinstance(data, list) else [], "raw": data}


def prompt_if_missing(args):
    search = args.search
    if not search:
        search = input("🔎 Chaîne de recherche (searchText) : ").strip()

    live = args.live
    if live is None:
        raw = input("📡 Mode live ? (true/false) : ").strip().lower()
        if raw in ("true", "t", "1", "yes", "y", "oui", "o"):
            live = True
        elif raw in ("false", "f", "0", "no", "n", "non"):
            live = False
        else:
            print("Valeur invalide pour live. Utilise true/false.")
            sys.exit(2)

    return search, live


def main():
    parser = argparse.ArgumentParser(description="Recherche de contrats TopstepX")
    parser.add_argument("--search", "-s", type=str, help="Texte à rechercher (searchText)")
    parser.add_argument("--live", "-l", type=lambda x: x.lower() in ("1", "true", "t", "yes", "y", "oui", "o"),
                        help="True pour live, False pour sim. Exemple: --live true")
    parser.add_argument("--output", "-o", type=str, help="Chemin de sortie (sinon config.paths.contract_file)")
    args = parser.parse_args()

    config = Config()

    # Sécurité sur paths.contract_file
    if not getattr(config, "paths", None) or "contract_file" not in config.paths:
        print("❌ config.paths.contract_file est manquant dans config.yaml")
        sys.exit(1)

    output_file = args.output or config.paths["contract_file"]

    # HttpBase peut exiger username; on le passe depuis la config.
    # Certaines implémentations attendent account_id en int.
    try:
        account_id = int(config.account_id) if config.account_id is not None else None
    except ValueError:
        account_id = config.account_id  # garde tel quel si non convertible

    http = HttpBase(
        base_url=config.base_url,
        api_key=config.api_key,
        endpoints=config.api_endpoints,
        account_id=account_id,
        username=getattr(config, "username", None),
        logging_enabled=True
    )

    search_text, live = prompt_if_missing(args)
    result = search_contracts(search_text, live, http)

    ensure_dir_exists(output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if result.get("success"):
        contracts = result.get("contracts", [])
        print(f"✅ {len(contracts)} contrat(s) trouvés. Résultat sauvegardé dans: {output_file}")
        for c in contracts[:5]:
            cid = c.get("id") or c.get("contractId") or c.get("symbol")
            name = c.get("name") or c.get("description") or ""
            print(f"  - {cid} | {name}")
        if len(contracts) > 5:
            print(f"  ... (+{len(contracts)-5} supplémentaires)")
    else:
        print(f"⚠️ Échec de la recherche. Détails sauvegardés dans: {output_file}")
        err = result.get("error") or result.get("response")
        if err:
            print(err)


if __name__ == "__main__":
    main()
