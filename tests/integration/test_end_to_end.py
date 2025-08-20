import yaml
from urdu_exec_bot.parsers.signal_csv import SignalCsvParser
from urdu_exec_bot.csv_watcher import CsvWatcher
from urdu_exec_bot.services.state_store import StateStore
from urdu_exec_bot.services.lot_sizing import LotSizing
from urdu_exec_bot.services.position_manager import PositionManager
from urdu_exec_bot.services.strategy_engine import StrategyEngine
from urdu_exec_bot.services.execution_service import ExecutionService
from urdu_exec_bot.services.risk_manager import RiskManager
from urdu_exec_bot.models.signal import Signal, SignalAction
from urdu_exec_bot.models.position import PositionSide


class DummyClient:
    def place_order(self, instrument, side, qty, order_type="MARKET", client_tag=None):
        return True, {}

    def search_open_orders(self):
        return True, {}

    def flat_position(self, instrument, qty, side_to_close, client_tag=None):
        return True, {}


def test_pipeline_and_risk_flat_all(settings_tmp, tmp_path):
    with open(settings_tmp["settings_path"], "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    state_store = StateStore(settings_path=str(settings_tmp["settings_path"]))
    state = state_store.load()
    parser = SignalCsvParser(settings=cfg)
    lots = LotSizing(settings_path=str(settings_tmp["settings_path"]))
    pm = PositionManager()
    strat = StrategyEngine(lot_sizing=lots, position_manager=pm)
    risk = RiskManager(settings_path=str(settings_tmp["settings_path"]))
    client = DummyClient()
    exec_svc = ExecutionService(client=client, lot_sizing=lots, unique_trade_at_a_time=True)

    s1 = Signal.create("GC", SignalAction.LONG)
    pos = state.get_position("GC")
    orders = strat.decide_orders(s1, pos)
    exec_svc.execute_signal_orders(state, orders)
    p = state.get_position("GC")
    assert p.side == PositionSide.LONG
    assert p.qty == 1

    s2 = Signal.create("GC", SignalAction.EXIT)
    pos = state.get_position("GC")
    orders2 = strat.decide_orders(s2, pos)
    exec_svc.execute_signal_orders(state, orders2)
    p2 = state.get_position("GC")
    assert p2.side == PositionSide.SHORT
    assert p2.qty == 1

    state.pnl_day = risk.threshold()
    if risk.should_flat_all(state):
        exec_svc.close_all(state)
    p3 = state.get_position("GC")
    assert p3.side == PositionSide.FLAT
    assert p3.qty == 0
