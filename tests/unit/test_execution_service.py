from urdu_exec_bot.services.execution_service import ExecutionService
from urdu_exec_bot.services.lot_sizing import LotSizing
from urdu_exec_bot.services.position_manager import PositionManager
from urdu_exec_bot.services.strategy_engine import StrategyEngine
from urdu_exec_bot.models.trade_state import TradeState
from urdu_exec_bot.models.signal import Signal, SignalAction


class DummyClient:
    def place_order(self, instrument, side, qty, order_type="MARKET", client_tag=None):
        return True, {"ok": True}

    def search_open_orders(self):
        return True, {}

    def search_open_positions(self):
        return True, {}

    def flat_position(self, instrument, qty, side_to_close, client_tag=None):
        return True, {}


def test_execute_and_close_all(settings_tmp):
    lots = LotSizing(settings_path=str(settings_tmp["settings_path"]))
    client = DummyClient()
    exec_svc = ExecutionService(client=client, lot_sizing=lots, unique_trade_at_a_time=True)
    pm = PositionManager()
    strat = StrategyEngine(lot_sizing=lots, position_manager=pm)
    state = TradeState()

    sig = Signal.create("GC", SignalAction.LONG)
    pos = state.get_position("GC")
    orders = strat.decide_orders(sig, pos)
    executed = exec_svc.execute_signal_orders(state, orders)
    assert len(executed) == 1
    p = state.get_position("GC")
    assert p.side.value == "LONG"
    assert p.qty == 1

    closed = exec_svc.close_all(state)
    assert len(closed) == 1
    p2 = state.get_position("GC")
    assert p2.side.value == "FLAT"
    assert p2.qty == 0
