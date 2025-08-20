from urdu_exec_bot.services.risk_manager import RiskManager
from urdu_exec_bot.models.trade_state import TradeState


def test_risk_threshold(settings_tmp):
    r = RiskManager(settings_path=str(settings_tmp["settings_path"]))
    s = TradeState()
    s.pnl_day = r.threshold() - 0.01
    assert r.should_flat_all(s) is False
    s.pnl_day = r.threshold()
    assert r.should_flat_all(s) is True
