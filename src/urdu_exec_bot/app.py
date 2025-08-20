import os
import time
import yaml
from pathlib import Path
from typing import Any, Dict
from .utils.logging_setup import setup_logging
from .csv_watcher import CsvWatcher
from .parsers.signal_csv import SignalCsvParser
from .services.state_store import StateStore
from .services.lot_sizing import LotSizing
from .services.position_manager import PositionManager
from .services.strategy_engine import StrategyEngine
from .services.execution_service import ExecutionService
from .services.risk_manager import RiskManager
from .services.topstepx_client import TopstepXClient


def load_settings() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    settings_path = os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run() -> None:
    settings = load_settings()
    root = Path(__file__).resolve().parents[2]
    settings_path = os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
    setup_logging(settings_path)

    state_store = StateStore(settings_path=settings_path)
    state = state_store.load()

    csv_path = settings.get("paths", {}).get("csv_input") or str(root / "data" / "input" / "signals.csv")
    watcher = CsvWatcher(csv_path=csv_path, state_store=state_store)
    parser = SignalCsvParser(settings=settings)

    lot_sizing = LotSizing(settings_path=settings_path)
    position_manager = PositionManager()
    strategy = StrategyEngine(lot_sizing=lot_sizing, position_manager=position_manager)
    risk = RiskManager(settings_path=settings_path)
    client = TopstepXClient(settings_path=settings_path)
    exec_service = ExecutionService(client=client, lot_sizing=lot_sizing, unique_trade_at_a_time=bool(settings.get("execution", {}).get("unique_trade_at_a_time", True)))

    interval_ms = int(settings.get("polling", {}).get("interval_ms", 500))
    try:
        while True:
            # Reset quotidien du mode évaluation (dégele le trading à l'heure configurée)
            risk.maybe_daily_reset(state)

            # Si on est gelé, s'assurer que tout est flat et ignorer les signaux
            if state.trading_halted_today:
                if risk.should_flat_all(state):
                    exec_service.close_all(state)
                state_store.save(state)
                time.sleep(max(0.0, interval_ms / 1000.0))
                continue

            lines = watcher.read_new_lines()
            for line in lines:
                sig = parser.parse_line(line)
                if not sig:
                    continue
                pos = state.get_position(sig.instrument)
                orders = strategy.decide_orders(sig, pos)
                if orders:
                    exec_service.execute_signal_orders(state, orders)

                # Après chaque exécution, vérifier si un halt évaluation doit s'appliquer
                just_halted = risk.check_and_mark_halt(state)
                if just_halted or risk.should_flat_all(state):
                    exec_service.close_all(state)
                    # si halt évaluation, on sort de la boucle de traitement de lignes
                    if state.trading_halted_today:
                        break

            state_store.save(state)
            time.sleep(max(0.0, interval_ms / 1000.0))
    except KeyboardInterrupt:
        state_store.save(state)


if __name__ == "__main__":
    run()
