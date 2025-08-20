#!/usr/bin/env python
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# --- ensure src on path ---
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# --- minimal .env loader (optional) ---
def _load_dotenv_if_needed() -> None:
    if "TOPSTEPX_API_KEY" in os.environ and "SETTINGS_PATH" in os.environ:
        return
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'").strip('"')
            os.environ.setdefault(k, v)
    except Exception:
        pass

_load_dotenv_if_needed()

import yaml  # noqa: E402

from urdu_exec_bot.services.topstepx_client import (  # noqa: E402
    TopstepXClient,
    TSOrderType,
    TSSide,
)


def load_settings(path: Optional[str]) -> Dict[str, Any]:
    if path:
        p = Path(path)
    else:
        p = Path(os.environ.get("SETTINGS_PATH", ROOT / "config" / "settings.yaml"))
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _unique_tag(base: str = "manual_test") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    rnd = uuid.uuid4().hex[:6]
    return f"{base}-{ts}-{rnd}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", type=str, default=os.environ.get("SETTINGS_PATH", str(ROOT / "config" / "settings.yaml")))
    ap.add_argument("-i", "--instrument", type=str, required=True)
    ap.add_argument("-s", "--side", type=str, choices=["BUY", "SELL", "buy", "sell"], required=True)
    ap.add_argument("-q", "--qty", type=int, default=1)
    ap.add_argument("-t", "--type", type=str, default="MARKET", choices=["MARKET", "LIMIT", "STOP", "TRAILING_STOP", "JOIN_BID", "JOIN_ASK"])
    ap.add_argument("-p", "--price", type=float, default=None)
    ap.add_argument("--tag", type=str, default=None)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()

    settings = load_settings(args.settings)
    client = TopstepXClient(settings_path=args.settings)

    cid = client.resolve_contract_id(args.instrument)
    if not cid:
        print(f"[ERROR] contractId introuvable pour instrument {args.instrument} (config topstepx.contracts).")
        sys.exit(2)

    side_str = args.side.upper()
    type_str = args.type.upper()
    side_code = int(TSSide.BUY if side_str == "BUY" else TSSide.SELL)
    type_code = int(getattr(TSOrderType, type_str).value)
    tag = args.tag or _unique_tag("manual_test")

    payload_preview = {
        "accountId": settings.get("topstepx", {}).get("account_id"),
        "username": settings.get("topstepx", {}).get("username"),
        "instrument": args.instrument,
        "contractId": cid,
        "side": side_str,   # lisible
        "type": type_str,   # lisible
        "size": int(args.qty),
        "customTag": tag,
    }
    if args.price is not None:
        payload_preview["price"] = args.price

    print("[INFO] Préparation de l'ordre:")
    for k, v in payload_preview.items():
        print(f"  {k}: {v}")

    if not args.live:
        print("[INFO] DRY-RUN: aucun envoi (ajoute --live pour placer l'ordre).")
        sys.exit(0)

    ok, data = client.place_order(
        instrument=args.instrument,
        side=side_str,
        qty=args.qty,
        order_type=type_str,
        client_tag=tag,
        extra={"price": args.price} if args.price is not None else None,
    )
    code = 0 if ok else 1
    print(f"[RESULT] ok={ok} data={data}")
    sys.exit(code)


if __name__ == "__main__":
    main()
