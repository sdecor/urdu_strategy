from __future__ import annotations

import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from .utils.logging_setup import setup_logging
from .csv_watcher import CsvWatcher
from .services.state_store import StateStore
from .services.topstepx_client import TopstepXClient, TSOrderType


# ----------------------------- util config -----------------------------

def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_settings() -> Dict[str, Any]:
    default_path = _project_root() / "config" / "settings.yaml"
    settings_path = Path(os.environ.get("SETTINGS_PATH", str(default_path)))
    with settings_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ----------------------------- parsing -----------------------------

@dataclass
class ParsedSignal:
    instrument: str
    action: str          # "BUY" / "SELL"
    lots_hint: int       # N (peut être négatif/positif/0)


_SIG_RE = re.compile(
    r".*?:\s*ordre\s*(?P<action>buy|sell)\s*@.*?\s*sur\s*(?P<ins>[A-Z0-9!]+)\s*!\s*\.?\s*La nouvelle position de la stratégie est\s*(?P<n>[-+]?\d+)",
    re.IGNORECASE,
)

_INS_RE = re.compile(r"\b([A-Z]{1,3}\d?!?)\b")
_NUM_RE = re.compile(r"(-?\d+)\s*$")


def parse_signal(raw: str) -> Optional[ParsedSignal]:
    if not raw:
        return None
    m = _SIG_RE.search(raw)
    if not m:
        act = "BUY" if "buy" in raw.lower() else ("SELL" if "sell" in raw.lower() else None)
        ins_m = _INS_RE.search(raw)
        num_m = _NUM_RE.search(raw.strip())
        if not (act and ins_m and num_m):
            return None
        ins = ins_m.group(1).upper()
        if not ins.endswith("!"):
            ins += "!"
        lots_hint = int(num_m.group(1))
        return ParsedSignal(instrument=ins, action=act.upper(), lots_hint=lots_hint)

    action = m.group("action").upper()
    instrument = m.group("ins").upper()
    if not instrument.endswith("!"):
        instrument += "!"
    lots_hint = int(m.group("n"))
    return ParsedSignal(instrument=instrument, action=action, lots_hint=lots_hint)


# ----------------------------- time filter (UTC minute match) -----------------------------

def _parse_utc(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    s = ts.strip()
    s = s.replace("Z", "+00:00")  # ISO Z to offset
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        pass
    # Fallbacks
    fmts = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt).astimezone(timezone.utc)
            return dt
        except Exception:
            continue
    return None


def _same_utc_minute(ts_str: str) -> bool:
    dt = _parse_utc(ts_str)
    if not dt:
        return False
    now_utc = datetime.now(timezone.utc)
    return dt.replace(second=0, microsecond=0) == now_utc.replace(second=0, microsecond=0)


# ----------------------------- execution helpers -----------------------------

def _state_is_halted(state: Dict[str, Any]) -> bool:
    return bool(state.get("evaluation", {}).get("halted", False))


def _set_state_halt(state: Dict[str, Any], halted: bool, reason: str = "") -> None:
    state.setdefault("evaluation", {})
    state["evaluation"]["halted"] = bool(halted)
    state["evaluation"]["halt_reason"] = str(reason or "")


def _lots_for(instrument: str, lots_cfg: Dict[str, Any]) -> int:
    lots = (lots_cfg.get("lots") or {}) if lots_cfg else {}
    return int(lots.get(instrument, lots.get("default", 1)))


def _contracts_map(settings: Dict[str, Any]) -> Dict[str, str]:
    return {str(k).upper(): str(v) for k, v in (settings.get("topstepx", {}).get("contracts") or {}).items()}


def _risk_close_all_reached(pnl_today: float, risk_cfg: Dict[str, Any]) -> bool:
    pnl = (risk_cfg.get("pnl") or {})
    thr = pnl.get("daily_close_all_when_gte")
    try:
        return thr is not None and float(pnl_today) >= float(thr)
    except Exception:
        return False


def _evaluation_halt_reached(pnl_today: float, risk_cfg: Dict[str, Any]) -> Tuple[bool, Optional[float]]:
    ev = (risk_cfg.get("evaluation") or {})
    if not bool(ev.get("enabled", False)):
        return False, None
    lim = ev.get("daily_max_gain_usd")
    try:
        if lim is not None and float(pnl_today) >= float(lim):
            return True, float(lim)
    except Exception:
        pass
    return False, None


# ----------------------------- decision (URDU) -----------------------------

@dataclass
class Decision:
    side: str
    qty: int
    reason: str  # pour logs


def decide_orders_urdu(parsed: ParsedSignal, lots_configured: int, current_side: str) -> Decision:
    """
    Règles (N = lots_hint de TradingView) :
      - N < 0  => flatten all : si LONG → SELL lots_configured ; si SHORT → BUY lots_configured ; FLAT → rien
      - N = 0  => un pas vers flat selon le message : SELL → SELL 1 ; BUY → BUY 1
      - N > 0  => ajout/ouverture dans le sens du message avec la taille configurée: 1 lot
    """
    act = parsed.action.upper()
    n = parsed.lots_hint
    lots = max(1, int(lots_configured))
    cs = current_side.upper()

    if n < 0:
        if cs == "LONG":
            return Decision("SELL", lots, f"flatten_all: LONG→SELL {lots}")
        if cs == "SHORT":
            return Decision("BUY", lots, f"flatten_all: SHORT→BUY {lots}")
        return Decision(act, 0, "flatten_all: already FLAT")

    if n == 0:
        if act == "SELL":
            return Decision("SELL", 1, "step_to_flat via SELL")
        if act == "BUY":
            return Decision("BUY", 1, "step_to_flat via BUY")
        return Decision(act, 0, "n=0 but unknown action")

    # n > 0
    if act == "SELL":
        return Decision("SELL", 1, "reinforce/open SELL by 1 (configured)")
    if act == "BUY":
        return Decision("BUY", 1, "reinforce/open BUY by 1 (configured)")
    return Decision(act, 0, "n>0 but unknown action")


# ----------------------------- app loop -----------------------------

def run() -> int:
    root = _project_root()

    try:
        setup_logging(str(root / "config" / "logging.yaml"))
    except Exception:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("urdu_exec_bot")

    settings = _load_settings()
    csv_cfg = settings.get("csv_reader", {}) or {}
    paths = settings.get("paths", {}) or {}
    csv_path = Path(paths.get("csv_input") or (root / "data" / "input" / "signals.csv"))

    state_store = StateStore()
    state = state_store.load()

    lots_cfg = {}
    lots_path = (settings.get("config_files", {}) or {}).get("lots")
    try:
        if lots_path:
            with Path(lots_path).open("r", encoding="utf-8") as f:
                lots_cfg = yaml.safe_load(f) or {}
    except Exception:
        lots_cfg = {}

    risk_cfg = {}
    risk_path = (settings.get("config_files", {}) or {}).get("risk")
    try:
        if risk_path:
            with Path(risk_path).open("r", encoding="utf-8") as f:
                risk_cfg = yaml.safe_load(f) or {}
    except Exception:
        risk_cfg = {}

    watcher = CsvWatcher(
        csv_path=csv_path,
        state_store=state_store,  # ignoré (compat)
        schema=csv_cfg.get("schema", ["received_at", "content_type", "raw"]),
        delimiter=str(csv_cfg.get("delimiter", ",")),
        has_header=bool(csv_cfg.get("has_header", True)),
    )

    client = TopstepXClient()

    log.info("URDU Exec Bot démarré (lecture dernière ligne uniquement). CSV: %s", csv_path)

    poll_ms = int((settings.get("polling", {}) or {}).get("interval_ms", 500))
    while True:
        try:
            pnl_today = float(state.get("pnl", {}).get("today", 0.0))
            if _risk_close_all_reached(pnl_today, risk_cfg):
                _set_state_halt(state, True, "daily_close_all_when_gte reached")
            ev_hit, lim = _evaluation_halt_reached(pnl_today, risk_cfg)
            if ev_hit:
                _set_state_halt(state, True, f"evaluation daily_max_gain_usd {lim} reached")

            if _state_is_halted(state):
                time.sleep(poll_ms / 1000.0)
                continue

            rec = watcher.read_latest_record()
            if not rec:
                time.sleep(poll_ms / 1000.0)
                continue

            # ---------------- UTC minute gate ----------------
            ra = (rec.get("received_at") or "").strip()
            if not _same_utc_minute(ra):
                time.sleep(poll_ms / 1000.0)
                continue
            # --------------------------------------------------

            raw = rec.get("raw", "")
            parsed = parse_signal(raw)
            if not parsed:
                time.sleep(poll_ms / 1000.0)
                continue

            ins = parsed.instrument
            lots_conf = _lots_for(ins, lots_cfg)
            cur = (state.get("positions", {}) or {}).get(ins, {"side": "FLAT", "size": 0})
            current_side = str(cur.get("side", "FLAT")).upper()

            decision = decide_orders_urdu(parsed, lots_conf, current_side)

            if decision.qty <= 0:
                logging.getLogger("urdu_exec_bot").info(
                    "Aucune action (%s %s) | current=%s | reason=%s",
                    parsed.action, parsed.lots_hint, current_side, decision.reason
                )
                time.sleep(poll_ms / 1000.0)
                continue

            contracts = _contracts_map(settings)
            if ins.upper() not in contracts or not contracts[ins.upper()] or contracts[ins.upper()].upper().startswith("REPLACE"):
                logging.getLogger("urdu_exec_bot").error(
                    "contractId manquant pour %s. Ordre non envoyé. reason=%s",
                    ins, decision.reason
                )
                time.sleep(poll_ms / 1000.0)
                continue

            logging.getLogger("urdu_exec_bot").info(
                "Placer ordre: %s %s sur %s (lots_cfg=%s | lots_hint=%s | current=%s) — %s",
                decision.side, decision.qty, ins, lots_conf, parsed.lots_hint, current_side, decision.reason
            )
            ok, data = client.place_order(
                instrument=ins,
                side=decision.side,
                qty=int(decision.qty),
                order_type=TSOrderType.MARKET,
                client_tag=f"urdu-{int(time.time())}",
            )
            if not ok:
                logging.getLogger("urdu_exec_bot").error("Order KO pour %s: %s", ins, data)
            else:
                logging.getLogger("urdu_exec_bot").info("Order OK pour %s: %s", ins, data)

            pos_map = state.setdefault("positions", {})
            if decision.side == "BUY":
                if current_side == "SHORT":
                    pos_map[ins] = {"side": "FLAT", "size": 0}
                else:
                    pos_map[ins] = {"side": "LONG", "size": cur.get("size", 0) + decision.qty}
            elif decision.side == "SELL":
                if current_side == "LONG":
                    pos_map[ins] = {"side": "FLAT", "size": 0}
                else:
                    pos_map[ins] = {"side": "SHORT", "size": cur.get("size", 0) + decision.qty}

            StateStore.save_static(state)

            time.sleep(poll_ms / 1000.0)

        except KeyboardInterrupt:
            logging.getLogger("urdu_exec_bot").info("Arrêt demandé (Ctrl+C).")
            break
        except Exception as e:
            logging.getLogger("urdu_exec_bot").exception("Boucle: exception: %s", e)
            time.sleep(1.0)

    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
