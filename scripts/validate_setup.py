#!/usr/bin/env python
import argparse
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import yaml
import requests


REQUIRED_TOPSTEPX_ENDPOINTS = [
    "login_key",
    "validate_token",
    "order_search",
    "order_search_open",
    "order_cancel",
    "position_search_open",
    "contract_available",
    "contract_search",
    "contract_search_by_id",
    "order_place",
    "account_search",
]


class CheckResult:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.infos: List[str] = []

    def ok(self) -> bool:
        return not self.errors

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.infos.append(msg)

    def dump(self) -> None:
        for m in self.infos:
            print(f"[OK] {m}")
        for w in self.warnings:
            print(f"[WARN] {w}")
        for e in self.errors:
            print(f"[ERROR] {e}")


def load_yaml(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data, ""
    except Exception as e:
        return {}, f"{type(e).__name__}: {e}"


def getenv_from_dotenv(dotenv_path: Path) -> Dict[str, str]:
    envs: Dict[str, str] = {}
    if not dotenv_path.exists():
        return envs
    try:
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                envs[k.strip()] = v.strip().strip("'").strip('"')
    except Exception:
        pass
    return envs


def check_python_version(cr: CheckResult) -> None:
    if sys.version_info < (3, 11):
        cr.add_error(f"Python >= 3.11 requis. Version détectée: {sys.version.split()[0]}")
    else:
        cr.add_info(f"Python OK: {sys.version.split()[0]}")


def check_settings_path(arg_settings: str) -> Path:
    if arg_settings:
        return Path(arg_settings)
    env = os.environ.get("SETTINGS_PATH", "")
    if env:
        return Path(env)
    return Path("config/settings.yaml")


def is_writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        testfile = path.parent / ".perm_test.tmp"
        with open(testfile, "w", encoding="utf-8") as f:
            f.write("ok")
        testfile.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def check_paths(cr: CheckResult, settings: Dict[str, Any], root: Path) -> None:
    paths = settings.get("paths", {}) or {}

    csv_input = Path(paths.get("csv_input") or (root / "data" / "input" / "signals.csv"))
    if not csv_input.exists():
        cr.add_warn(f"CSV d'entrée absent: {csv_input} (le fichier sera créé au premier run).")
    if not is_writable(csv_input):
        cr.add_error(f"Droits insuffisants pour écrire dans le dossier du CSV: {csv_input.parent}")
    else:
        cr.add_info(f"Chemin CSV OK: {csv_input}")

    archive_dir = Path(paths.get("archive_dir") or (root / "data" / "archive"))
    if not archive_dir.exists():
        cr.add_warn(f"Dossier archive absent: {archive_dir}")
    if not is_writable(archive_dir / ".perm"):
        cr.add_error(f"Droits insuffisants sur archive_dir: {archive_dir}")
    else:
        cr.add_info(f"Archive dir OK: {archive_dir}")

    logs_dir = Path(paths.get("logs_dir") or (root / "logs"))
    if not logs_dir.exists():
        cr.add_warn(f"Dossier logs absent: {logs_dir}")
    if not is_writable(logs_dir / ".perm"):
        cr.add_error(f"Droits insuffisants sur logs_dir: {logs_dir}")
    else:
        cr.add_info(f"Logs dir OK: {logs_dir}")

    state = paths.get("state", {}) or {}
    trade_state = Path(state.get("trade_state") or (root / "state" / "trade_state.json"))
    offset = Path(state.get("offset") or (root / "state" / "offsets" / "signals.offset"))
    if not is_writable(trade_state):
        cr.add_error(f"Droits insuffisants pour écrire l'état: {trade_state}")
    else:
        cr.add_info(f"State file OK (writable): {trade_state}")
    if not is_writable(offset):
        cr.add_error(f"Droits insuffisants pour écrire l'offset: {offset}")
    else:
        cr.add_info(f"Offset file OK (writable): {offset}")


def check_config_files(cr: CheckResult, settings: Dict[str, Any], root: Path) -> Tuple[Path, Path, Path]:
    cfgs = settings.get("config_files", {}) or {}
    lots_path = Path(cfgs.get("lots") or (root / "config" / "instruments_lots.yaml"))
    risk_path = Path(cfgs.get("risk") or (root / "config" / "risk.yaml"))
    logging_path = Path(cfgs.get("logging") or (root / "config" / "logging.yaml"))

    for pth, name in [(lots_path, "instruments_lots.yaml"), (risk_path, "risk.yaml"), (logging_path, "logging.yaml")]:
        if not pth.exists():
            cr.add_error(f"Fichier de config manquant: {name} ({pth})")
        else:
            cr.add_info(f"Fichier de config OK: {pth}")

    lots, err = load_yaml(lots_path) if lots_path.exists() else ({}, "")
    if lots_path.exists():
        lots_map = (lots.get("lots") or {})
        if not isinstance(lots_map, dict) or not lots_map:
            cr.add_error(f"Config lots invalide: 'lots' doit être un dict non vide ({lots_path})")
        elif "default" not in lots_map:
            cr.add_warn(f"'lots.default' manquant ({lots_path})")
        else:
            cr.add_info("Lots OK")

    risk, err = load_yaml(risk_path) if risk_path.exists() else ({}, "")
    if risk_path.exists():
        pnl = (risk.get("pnl") or {})
        if not isinstance(pnl, dict) or "daily_close_all_when_gte" not in pnl:
            cr.add_warn(f"Paramètre 'pnl.daily_close_all_when_gte' manquant dans {risk_path}")
        eval_cfg = (risk.get("evaluation") or {})
        if eval_cfg:
            if not isinstance(eval_cfg, dict):
                cr.add_error(f"'evaluation' doit être un objet ({risk_path})")
            else:
                if eval_cfg.get("enabled", False) and not eval_cfg.get("daily_max_gain_usd"):
                    cr.add_error(f"'evaluation.enabled' est true mais 'evaluation.daily_max_gain_usd' est vide ({risk_path})")
        trading = (risk.get("trading") or {})
        if trading and "allowed_instruments" in trading and not trading["allowed_instruments"]:
            cr.add_warn("Liste 'trading.allowed_instruments' vide.")

    logging_cfg, err = load_yaml(logging_path) if logging_path.exists() else ({}, "")
    if logging_path.exists():
        if not isinstance(logging_cfg, dict) or "version" not in logging_cfg:
            cr.add_warn("logging.yaml: champ 'version' manquant.")
        else:
            cr.add_info("Logging config OK")

    return lots_path, risk_path, logging_path


def check_csv_reader(cr: CheckResult, settings: Dict[str, Any]) -> None:
    csvr = settings.get("csv_reader", {}) or {}
    schema = csvr.get("schema") or []
    if not schema:
        cr.add_error("csv_reader.schema manquant.")
    else:
        target_schema = ["received_at", "content_type", "raw"]
        if [s.lower() for s in schema] != target_schema:
            cr.add_warn(f"csv_reader.schema attendu {target_schema}, trouvé {schema}.")
        else:
            cr.add_info("CSV schema OK (received_at, content_type, raw).")

    delim = str(csvr.get("delimiter", ","))
    if not delim:
        cr.add_warn("csv_reader.delimiter vide.")
    else:
        cr.add_info(f"CSV delimiter OK: '{delim}'")

    has_header = bool(csvr.get("has_header", True))
    cr.add_info(f"CSV has_header: {has_header}")


def check_topstepx(cr: CheckResult, settings: Dict[str, Any], dotenv_envs: Dict[str, str]) -> Dict[str, Any]:
    ts = settings.get("topstepx", {}) or {}
    base_url = str(ts.get("base_url") or "").strip()
    account_id = str(ts.get("account_id") or "").strip()
    username = str(ts.get("username") or "").strip()
    auth = ts.get("auth", {}) or {}
    endpoints = ts.get("endpoints", {}) or {}
    contracts = {str(k).upper(): str(v) for k, v in (ts.get("contracts") or {}).items()}

    if not base_url or not base_url.lower().startswith(("http://", "https://")):
        cr.add_error("topstepx.base_url invalide ou vide.")
    else:
        cr.add_info(f"TopstepX base_url OK: {base_url}")

    if not account_id:
        cr.add_error("topstepx.account_id manquant.")
    else:
        cr.add_info(f"TopstepX account_id OK: {account_id}")

    if not username:
        cr.add_warn("topstepx.username vide (recommandé).")
    else:
        cr.add_info(f"TopstepX username OK: {username}")

    api_key_env = str(auth.get("api_key_env") or "TOPSTEPX_API_KEY")
    api_key = os.environ.get(api_key_env) or dotenv_envs.get(api_key_env, "")
    if not api_key:
        cr.add_error(f"Variable d'environnement '{api_key_env}' introuvable ou vide (mettre la clé API).")
    else:
        masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        cr.add_info(f"API key détectée via {api_key_env}: {masked}")

    missing = [k for k in REQUIRED_TOPSTEPX_ENDPOINTS if k not in endpoints]
    if missing:
        cr.add_warn(f"Endpoints manquants dans topstepx.endpoints: {missing}")
    else:
        cr.add_info("TopstepX endpoints OK")

    if not contracts:
        cr.add_warn("topstepx.contracts vide (map instrument -> contractId).")
    else:
        for ins, cid in contracts.items():
            if not cid or cid.upper().startswith("REPLACE"):
                cr.add_warn(f"ContractId manquant pour {ins} dans topstepx.contracts.")
        if "UB1!" in contracts and contracts["UB1!"]:
            cr.add_info(f"ContractId UB1! OK: {contracts['UB1!']}")

    return {
        "base_url": base_url,
        "account_id": account_id,
        "username": username,
        "api_key": api_key,
        "endpoints": endpoints,
        "contracts": contracts,
        "api_key_env": api_key_env,
    }


def _headers(token: str) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def api_login_key(cr: CheckResult, cfg: Dict[str, Any], timeout: int = 15) -> Tuple[Optional[str], Dict[str, Any]]:
    url = f"{cfg['base_url'].rstrip('/')}{cfg['endpoints'].get('login_key', '/api/Auth/loginKey')}"
    payload = {"userName": cfg["username"], "apiKey": cfg["api_key"]}
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
        data = resp.json() if resp.content else {}
        if 200 <= resp.status_code < 300 and bool(data.get("success")) and data.get("token"):
            cr.add_info("Auth loginKey OK (token reçu).")
            return str(data["token"]), data
        cr.add_error(f"Auth loginKey KO ({resp.status_code}) {url} ⇒ {data}")
        return None, data
    except Exception as e:
        cr.add_error(f"Auth loginKey exception ⇒ {e}")
        return None, {"error": str(e)}


def api_validate_token(cr: CheckResult, cfg: Dict[str, Any], token: str, timeout: int = 10) -> None:
    url = f"{cfg['base_url'].rstrip('/')}{cfg['endpoints'].get('validate_token', '/api/Auth/validate')}"
    try:
        resp = requests.post(url, json={}, headers=_headers(token), timeout=timeout)
        if 200 <= resp.status_code < 300:
            cr.add_info("Auth validate OK.")
        else:
            content = resp.json() if resp.content else {}
            cr.add_warn(f"Auth validate KO ({resp.status_code}) ⇒ {content}")
    except Exception as e:
        cr.add_warn(f"Auth validate exception ⇒ {e}")


def api_probe_topstepx(cr: CheckResult, cfg: Dict[str, Any], token: str, timeout: int = 15, safe_only: bool = True) -> None:
    base_url = cfg["base_url"].rstrip("/")
    eps = cfg["endpoints"]
    account_id = cfg["account_id"]

    def _post(name: str, payload: Dict[str, Any]) -> Tuple[int, Any, str]:
        url = f"{base_url}{eps.get(name, '')}"
        try:
            resp = requests.post(url, json=payload, headers=_headers(token), timeout=timeout)
            content = {}
            if resp.content:
                try:
                    content = resp.json()
                except Exception:
                    content = resp.text
            return resp.status_code, content, url
        except Exception as e:
            return 0, {"error": str(e)}, url

    code, data, url = _post("account_search", {"onlyActiveAccounts": True})
    if 200 <= code < 300:
        cr.add_info(f"API account_search OK ({code}) {url}")
    else:
        cr.add_error(f"API account_search KO ({code}) {url} ⇒ {data}")

    code, data, url = _post("position_search_open", {"accountId": account_id})
    if 200 <= code < 300:
        cr.add_info(f"API position_search_open OK ({code}) {url}")
    else:
        cr.add_error(f"API position_search_open KO ({code}) {url} ⇒ {data}")

    code, data, url = _post("order_search_open", {"accountId": account_id})
    if 200 <= code < 300:
        cr.add_info(f"API order_search_open OK ({code}) {url}")
    else:
        cr.add_error(f"API order_search_open KO ({code}) {url} ⇒ {data}")

    code, data, url = _post("contract_available", {"live": True})
    if 200 <= code < 300:
        cr.add_info(f"API contract_available OK ({code}) {url}")
    else:
        cr.add_warn(f"API contract_available KO ({code}) {url} ⇒ {data}")

    if not safe_only:
        code, data, url = _post("order_search", {"accountId": account_id})
        if 200 <= code < 300:
            cr.add_info(f"API order_search OK ({code}) {url}")
        else:
            cr.add_warn(f"API order_search KO ({code}) {url} ⇒ {data}")


def check_project_layout(cr: CheckResult, root: Path) -> None:
    expected = [
        root / "src" / "urdu_exec_bot" / "app.py",
        root / "src" / "urdu_exec_bot" / "services" / "risk_manager.py",
        root / "src" / "urdu_exec_bot" / "services" / "topstepx_client.py",
        root / "src" / "urdu_exec_bot" / "parsers" / "signal_csv.py",
        root / "config" / "settings.yaml",
        root / "config" / "risk.yaml",
    ]
    for p in expected:
        if not p.exists():
            cr.add_warn(f"Fichier attendu manquant: {p}")
        else:
            cr.add_info(f"Présent: {p}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation du setup URDU Exec Bot")
    parser.add_argument("--settings", type=str, default="", help="Chemin vers config/settings.yaml (sinon SETTINGS_PATH ou défaut).")
    parser.add_argument("--strict", action="store_true", help="Traite les warnings comme des erreurs (exit code 1 si warning).")
    parser.add_argument("--json", action="store_true", help="Sortie JSON machine-readable.")
    parser.add_argument("--no-api-check", action="store_true", help="Désactive les appels API live TopstepX.")
    parser.add_argument("--api-timeout", type=int, default=15, help="Timeout des requêtes API (secondes).")
    args = parser.parse_args()

    cr = CheckResult()
    check_python_version(cr)

    root = Path(__file__).resolve().parents[1]
    settings_path = check_settings_path(args.settings)
    if not settings_path.exists():
        cr.add_error(f"Fichier settings.yaml introuvable: {settings_path}")
        cr.dump()
        sys.exit(1)

    settings, err = load_yaml(settings_path)
    if err:
        cr.add_error(f"Erreur de lecture YAML settings: {err}")
        cr.dump()
        sys.exit(1)

    tz = settings.get("timezone", "")
    if not tz:
        cr.add_warn("Paramètre 'timezone' manquant dans settings.yaml.")
    else:
        cr.add_info(f"Timezone OK: {tz}")

    cfgs = settings.get("config_files", {}) or {}
    for key in ("lots", "risk", "logging"):
        if key not in cfgs:
            cr.add_warn(f"'config_files.{key}' manquant dans settings.yaml.")

    check_paths(cr, settings, root)
    check_config_files(cr, settings, root)
    check_csv_reader(cr, settings)

    dotenv_envs = getenv_from_dotenv(root / ".env")
    if dotenv_envs:
        cr.add_info(".env détecté à la racine.")
    else:
        cr.add_warn(".env absent à la racine (copier .env.example → .env et renseigner la clé).")

    ts_cfg = check_topstepx(cr, settings, dotenv_envs)
    check_project_layout(cr, root)

    session_token: Optional[str] = None
    if not args.no_api_check:
        if ts_cfg.get("base_url") and ts_cfg.get("username") and ts_cfg.get("api_key"):
            session_token, _ = api_login_key(cr, ts_cfg, timeout=args.api_timeout)
            if session_token:
                api_validate_token(cr, ts_cfg, session_token, timeout=args.api_timeout)
                api_probe_topstepx(cr, ts_cfg, session_token, timeout=args.api_timeout, safe_only=True)
        else:
            cr.add_warn("API check ignoré: base_url/username/api_key incomplets.")

    if args.json:
        out = {
            "ok": cr.ok() and (not args.strict or (args.strict and not cr.warnings)),
            "errors": cr.errors,
            "warnings": cr.warnings,
            "infos": cr.infos,
            "settings_path": str(settings_path),
            "api_checked": not args.no_api_check,
            "has_session_token": bool(session_token),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0 if out["ok"] else 1)

    cr.dump()
    if cr.errors:
        sys.exit(1)
    if args.strict and cr.warnings:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
