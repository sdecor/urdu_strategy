from urdu_exec_bot.services.lot_sizing import LotSizing
from urdu_exec_bot.services.position_manager import PositionManager
from urdu_exec_bot.services.strategy_engine import StrategyEngine
from urdu_exec_bot.models.signal import Signal, SignalAction
from urdu_exec_bot.models.trade_state import TradeState
from urdu_exec_bot.models.position import PositionSide


def test_long_from_flat_produces_buy(settings_tmp):
    lots = LotSizing(settings_path=str(settings_tmp["settings_path"]))
    pm = PositionManager()
    strat = StrategyEngine(lot_sizing=lots, position_manager=pm)
    state = TradeState()
    pos = state.get_position("GC")
    sig = Signal.create("GC", SignalAction.LONG)
    orders = strat.decide_orders(sig, pos)
    assert len(orders) == 1
    o = orders[0]
    assert o.instrument == "GC"
    assert o.side.value == "BUY"
    assert o.qty == 1


def test_exit_from_long_flips_to_short(settings_tmp):
    lots = LotSizing(settings_path=str(settings_tmp["settings_path"]))
    pm = PositionManager()
    strat = StrategyEngine(lot_sizing=lots, position_manager=pm)
    state = TradeState()
    pos = state.get_position("GC")
    pos.side = PositionSide.LONG
    pos.qty = 1
    sig = Signal.create("GC", SignalAction.EXIT)
    orders = strat.decide_orders(sig, pos)
    assert len(orders) == 2
    assert orders[0].side.value == "SELL"
    assert orders[0].qty == 1
    assert orders[1].side.value == "SELL"
    assert orders[1].qty == 1
