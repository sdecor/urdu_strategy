#!/usr/bin/env python
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- project root / env ---
ROOT = Path(__file__).resolve().parents[1]
SETTINGS_DEFAULT = ROOT / "config" / "settings.yaml"

def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))
    except Exception:
        pass

_load_dotenv()

# --- imports after env ---
import yaml  # noqa: E402
import requests  # noqa: E402


# --------------------------- helpers ---------------------------

def _load_settings(path: Optional[str]) -> Dict[str, Any]:
    p = Path(path or os.environ.get("SETTINGS_PATH", str(SETTINGS_DEFAULT)))
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _headers(token: Optional[str]) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _url(base: str, endpoints: Dict[str, str], name: str, fallback: str) -> str:
    return f"{base.rstrip('/')}{endpoints.get(name, fallback)}"


def _post(url: str, token: Optional[str], payload: Dict[str, Any], timeout: int = 20) -> Tuple[int, Any]:
    try:
        resp = requests.post(url, json=payload, headers=_headers(token), timeout=timeout)
        data = {}
        if resp.content:
            try:
                data = resp.json()
            except Exception:
                data = resp.text
        return resp.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}


def _print_table(rows: List[Dict[str, Any]], fields: List[str]) -> None:
    if not rows:
        print("(vide)")
        return
    # keep only present fields
    present = [f for f in fields if any(f in r for r in rows)]
    if not present:
        # show keys of first row
        present = list(rows[0].keys())
    # widths
    widths = {f: max(len(str(f)), *(len(str(r.get(f, ""))) for r in rows)) for f in present}
    # header
    hdr = " | ".join(f.ljust(widths[f]) for f in present)
    sep = "-+-".join("-" * widths[f] for f in present)
    print(hdr)
    print(sep)
    for r in rows:
        print(" | ".join(str(r.get(f, "")).ljust(widths[f]) for f in present))


def _normalize_contract_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # Many APIs; try map to stable keys
    return {
        "contractId": row.get("contractId") or row.get("id") or row.get("contractID") or row.get("ContractId"),
        "symbol": row.get("symbol") or row.get("Symbol") or row.get("ticker") or row.get("code"),
        "root": row.get("root") or row.get("rootSymbol") or row.get("root_code"),
        "name": row.get("name") or row.get("description") or row.get("displayName") or row.get("ContractName"),
        "exchange": row.get("exchange") or row.get("venue") or row.get("Exchange"),
        "currency": row.get("currency") or row.get("Currency"),
    }


def _normalize_account_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "accountId": row.get("accountId") or row.get("id") or row.get("AccountId"),
        "name": row.get("name") or row.get("accountName") or row.get("displayName"),
        "status": row.get("status") or row.get("state"),
        "type": row.get("type") or row.get("accountType"),
    }


# --------------------------- auth ---------------------------

def login_key(base_url: str, endpoints: Dict[str, str], username: str, api_key: str, timeout: int = 20) -> Tuple[Optional[str], Dict[str, Any]]:
    url = _url(base_url, endpoints, "login_key", "/api/Auth/loginKey")
    code, data = _post(url, None, {"userName": username, "apiKey": api_key}, timeout=timeout)
    if 200 <= code < 300 and isinstance(data, dict) and data.get("success") and data.get("token"):
        return str(data["token"]), data
    return None, {"code": code, "data": data}


def validate_token(base_url: str, endpoints: Dict[str, str], token: str, timeout: int = 10) -> Tuple[bool, Any]:
    url = _url(base_url, endpoints, "validate_token", "/api/Auth/validate")
    code, data = _post(url, token, {}, timeout=timeout)
    return (200 <= code < 300), {"code": code, "data": data}


# --------------------------- API ops ---------------------------

def list_accounts(base_url: str, endpoints: Dict[str, str], token: str, active_only: bool, timeout: int = 20) -> Tuple[bool, List[Dict[str, Any]], Any]:
    url = _url(base_url, endpoints, "account_search", "/api/Account/search")
    payload = {"onlyActiveAccounts": bool(active_only)}
    code, data = _post(url, token, payload, timeout=timeout)
    if 200 <= code < 300 and isinstance(data, (list, dict)):
        rows = data if isinstance(data, list) else data.get("accounts") or data.get("items") or []
        return True, [ _normalize_account_row(r) for r in rows ], {"code": code}
    return False, [], {"code": code, "data": data}


def contracts_available(base_url: str, endpoints: Dict[str, str], token: str, live: Optional[bool], timeout: int = 30) -> Tuple[bool, List[Dict[str, Any]], Any]:
    url = _url(base_url, endpoints, "contract_available", "/api/Contract/available")
    payload: Dict[str, Any] = {}
    if live is not None:
        payload["live"] = bool(live)
    code, data = _post(url, token, payload, timeout=timeout)
    if 200 <= code < 300 and isinstance(data, (list, dict)):
        rows = data if isinstance(data, list) else data.get("contracts") or data.get("items") or []
        return True, [ _normalize_contract_row(r) for r in rows ], {"code": code}
    return False, [], {"code": code, "data": data}


def contracts_search(base_url: str, endpoints: Dict[str, str], token: str, query: str, timeout: int = 30) -> Tuple[bool, List[Dict[str, Any]], Any]:
    url = _url(base_url, endpoints, "contract_search", "/api/Contract/search")
    payload = {"query": query}
    code, data = _post(url, token, payload, timeout=timeout)
    if 200 <= code < 300 and isinstance(data, (list, dict)):
        rows = data if isinstance(data, list) else data.get("contracts") or data.get("items") or []
        return True, [ _normalize_contract_row(r) for r in rows ], {"code": code}
    return False, [], {"code": code, "data": data}


def contracts_find_any(base_url: str, endpoints: Dict[str, str], token: str, needle: str, timeout: int = 30) -> Tuple[bool, List[Dict[str, Any]], Any]:
    ok, rows, meta = contracts_search(base_url, endpoints, token, needle, timeout=timeout)
    if ok and rows:
        return True, rows, meta
    # fallback: available + client-side filter
    ok2, allrows, meta2 = contracts_available(base_url, endpoints, token, live=None, timeout=timeout)
    if not ok2:
        return False, [], meta2
    n = needle.lower()
    filtered = []
    for r in allrows:
        if any(n in str(r.get(k, "")).lower() for k in ("contractId", "symbol", "root", "name", "exchange")):
            filtered.append(r)
    return True, filtered, meta2


# --------------------------- CLI ---------------------------

def main() -> None:
    ap = argparse.ArgumentParser(prog="topstepx_tool", description="Outils TopstepX: contrats & comptes")
    ap.add_argument("--settings", type=str, default=os.environ.get("SETTINGS_PATH", str(SETTINGS_DEFAULT)))
    ap.add_argument("--timeout", type=int, default=20)
    sub = ap.add_subparsers(dest="cmd", required=True)

    acc = sub.add_parser("accounts", help="Lister les comptes")
    acc.add_argument("--all", action="store_true", help="Inclure comptes inactifs")
    acc.add_argument("--json", action="store_true")
    acc.add_argument("--save", type=str, default="")

    con = sub.add_parser("contracts", help="Lister les contrats disponibles")
    con.add_argument("--live", type=str, choices=["true", "false", "auto"], default="auto")
    con.add_argument("--filter", type=str, default="")
    con.add_argument("--limit", type=int, default=50)
    con.add_argument("--json", action="store_true")
    con.add_argument("--save", type=str, default="")

    find = sub.add_parser("find", help='Rechercher un contrat (ex: "UB", "GC1!", contractId, etc.)')
    find.add_argument("-q", "--query", type=str, required=True)
    find.add_argument("--limit", type=int, default=20)
    find.add_argument("--json", action="store_true")
    find.add_argument("--save", type=str, default="")

    args = ap.parse_args()

    settings = _load_settings(args.settings)
    ts = settings.get("topstepx", {}) or {}
    base_url = str(ts.get("base_url") or "").strip()
    endpoints = ts.get("endpoints", {}) or {}
    username = str(ts.get("username") or "").strip()
    api_key_env = str((ts.get("auth", {}) or {}).get("api_key_env") or "TOPSTEPX_API_KEY")
    api_key = os.environ.get(api_key_env, "")

    if not base_url or not username or not api_key:
        print("[ERROR] Config/API key manquante: base_url/username/api_key", file=sys.stderr)
        sys.exit(2)

    token, auth_data = login_key(base_url, endpoints, username, api_key, timeout=args.timeout)
    if not token:
        print(f"[ERROR] Auth KO ⇒ {auth_data}", file=sys.stderr)
        sys.exit(3)

    # Optional validate (ignore result)
    _ = validate_token(base_url, endpoints, token, timeout=10)

    if args.cmd == "accounts":
        ok, rows, meta = list_accounts(base_url, endpoints, token, active_only=(not args.all), timeout=args.timeout)
        if not ok:
            print(f"[ERROR] accounts ⇒ {meta}", file=sys.stderr)
            sys.exit(4)
        if args.json or args.save:
            payload = {"items": rows, "meta": meta}
            s = json.dumps(payload, ensure_ascii=False, indent=2)
            if args.save:
                Path(args.save).write_text(s, encoding="utf-8")
                print(f"[SAVED] {args.save}")
            if args.json:
                print(s)
        else:
            _print_table(rows, ["accountId", "name", "status", "type"])

    elif args.cmd == "contracts":
        live = None if args.live == "auto" else (args.live == "true")
        ok, rows, meta = contracts_available(base_url, endpoints, token, live=live, timeout=args.timeout)
        if not ok:
            print(f"[ERROR] contracts ⇒ {meta}", file=sys.stderr)
            sys.exit(5)
        if args.filter:
            f = args.filter.lower()
            rows = [r for r in rows if any(f in str(r.get(k, "")).lower() for k in ("contractId", "symbol", "root", "name", "exchange"))]
        if args.limit and len(rows) > args.limit:
            rows = rows[:args.limit]
        if args.json or args.save:
            payload = {"items": rows, "meta": meta}
            s = json.dumps(payload, ensure_ascii=False, indent=2)
            if args.save:
                Path(args.save).write_text(s, encoding="utf-8")
                print(f"[SAVED] {args.save}")
            if args.json:
                print(s)
        else:
            _print_table(rows, ["contractId", "symbol", "root", "name", "exchange", "currency"])

    elif args.cmd == "find":
        ok, rows, meta = contracts_find_any(base_url, endpoints, token, args.query, timeout=args.timeout)
        if not ok:
            print(f"[ERROR] find ⇒ {meta}", file=sys.stderr)
            sys.exit(6)
        if args.limit and len(rows) > args.limit:
            rows = rows[:args.limit]
        if args.json or args.save:
            payload = {"items": rows, "meta": meta, "query": args.query}
            s = json.dumps(payload, ensure_ascii=False, indent=2)
            if args.save:
                Path(args.save).write_text(s, encoding="utf-8")
                print(f"[SAVED] {args.save}")
            if args.json:
                print(s)
        else:
            _print_table(rows, ["contractId", "symbol", "root", "name", "exchange", "currency"])

    else:
        print("[ERROR] commande inconnue", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
