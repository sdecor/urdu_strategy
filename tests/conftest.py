import os
import sys
from pathlib import Path
import pytest
import yaml


@pytest.fixture(scope="session", autouse=True)
def _ensure_src_on_path():
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    sys.path.insert(0, str(src))


@pytest.fixture()
def settings_tmp(tmp_path, monkeypatch):
    root = tmp_path
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "data" / "input").mkdir(parents=True, exist_ok=True)
    (root / "data" / "archive").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "state" / "offsets").mkdir(parents=True, exist_ok=True)

    settings = {
        "app_name": "urdu_exec_bot",
        "strategy": "URDU",
        "timezone": "Europe/Zurich",
        "paths": {
            "csv_input": str(root / "data" / "input" / "signals.csv"),
            "archive_dir": str(root / "data" / "archive"),
            "logs_dir": str(root / "logs"),
            "state": {
                "trade_state": str(root / "state" / "trade_state.json"),
                "offset": str(root / "state" / "offsets" / "signals.offset"),
            },
        },
        "config_files": {
            "lots": str(root / "config" / "instruments_lots.yaml"),
            "risk": str(root / "config" / "risk.yaml"),
            "logging": str(root / "config" / "logging.yaml"),
        },
        "polling": {"interval_ms": 10},
        "csv_reader": {
            "start_from_end": True,
            "delimiter": ",",
            "has_header": False,
            "schema": ["instrument", "action"],
            "action_mapping": {"long": "LONG", "buy": "LONG", "short": "SHORT", "sell": "SHORT", "exit": "EXIT"},
        },
        "execution": {"unique_trade_at_a_time": True},
        "topstepx": {
            "base_url": "http://localhost",
            "account_id": "TEST",
            "auth": {"api_key_env": "TOPSTEPX_API_KEY"},
            "endpoints": {
                "login_key": "/api/Auth/loginKey",
                "order_search": "/api/Order/search",
                "order_search_open": "/api/Order/searchOpen",
                "order_cancel": "/api/Order/cancel",
                "position_search_open": "/api/Position/searchOpen",
                "contract_available": "/api/Contract/available",
                "contract_search": "/api/Contract/search",
                "contract_search_by_id": "/api/Contract/searchById",
                "order_place": "/api/Order/place",
                "account_search": "/api/Account/search",
            },
        },
    }
    with open(root / "config" / "settings.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False)

    lots = {"lots": {"default": 1, "GC": 1, "UB": 2}}
    with open(root / "config" / "instruments_lots.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(lots, f, sort_keys=False)

    risk = {"pnl": {"daily_close_all_when_gte": 2000}}
    with open(root / "config" / "risk.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(risk, f, sort_keys=False)

    logging_cfg = {
        "version": 1,
        "handlers": {"console": {"class": "logging.StreamHandler", "level": "INFO"}},
        "root": {"level": "WARNING", "handlers": ["console"]},
    }
    with open(root / "config" / "logging.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(logging_cfg, f, sort_keys=False)

    with open(root / "state" / "trade_state.json", "w", encoding="utf-8") as f:
        f.write('{"positions": {}, "pnl_day": 0.0}')
    with open(root / "state" / "offsets" / "signals.offset", "w", encoding="utf-8") as f:
        f.write("0")

    monkeypatch.setenv("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
    return {"root": root, "settings_path": root / "config" / "settings.yaml"}
