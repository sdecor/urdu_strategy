# tests/test_risk_guard.py
from risk.risk_guard import RiskGuard
import types


def test_risk_guard_max_order_size(config):
    config.config["risk"] = {"max_order_size": 2}
    rg = RiskGuard(config, logging_enabled=False)
    ok, reason = rg.can_enter({"id": "any"}, side=0, total_lots=3)
    assert ok is False
    assert "max_order_size_exceeded" in reason


def test_risk_guard_min_minutes_before_stop(config, monkeypatch):
    # set stop_utc and min_minutes_before_stop
    config.trading_hours = {"start_utc": "00:00", "stop_utc": "20:05"}
    config.config["risk"] = {"min_minutes_before_stop": 5}

    rg = RiskGuard(config, logging_enabled=False)

    # Monkeypatch helper _minutes_until to return small positive number
    import risk.risk_guard as rgmod
    monkeypatch.setattr(rgmod, "_minutes_until", lambda now, t: 3)

    ok, reason = rg.can_enter({"id": "any"}, side=0, total_lots=1)
    assert ok is False
    assert "too_close_to_stop" in reason


def test_risk_guard_ok(config, monkeypatch):
    config.trading_hours = {"start_utc": "00:00", "stop_utc": "20:05"}
    config.config["risk"] = {"max_order_size": 10, "min_minutes_before_stop": 5}

    rg = RiskGuard(config, logging_enabled=False)

    import risk.risk_guard as rgmod
    monkeypatch.setattr(rgmod, "_minutes_until", lambda now, t: 30)

    ok, reason = rg.can_enter({"id": "ok"}, side=1, total_lots=3)
    assert ok is True
