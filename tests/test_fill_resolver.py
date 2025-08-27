# tests/test_fill_resolver.py
from fills.fill_resolver import FillResolver


def test_fill_resolver_from_positions_direct(config, monkeypatch):
    class Engine:
        def get_open_positions(self):
            return [{"contractId": config.contract_id, "size": 2, "averagePrice": 117.0}]

    # no sleep during tests
    monkeypatch.setattr("fills.fill_resolver.time.sleep", lambda *_args, **_kw: None)

    fr = FillResolver(Engine(), config, logging_enabled=False)
    price = fr.get_fill_price(config.contract_id)
    assert price == 117.0


def test_fill_resolver_retries_then_success(config, monkeypatch):
    calls = {"n": 0}

    class Engine:
        def get_open_positions(self):
            calls["n"] += 1
            if calls["n"] < 3:
                return []  # first two attempts: nothing
            return [{"contractId": config.contract_id, "size": 1, "averagePrice": 116.875}]

    # speed up
    monkeypatch.setattr("fills.fill_resolver.time.sleep", lambda *_args, **_kw: None)

    # ensure enough retries
    config.config["fills"]["retries"] = 5
    fr = FillResolver(Engine(), config, logging_enabled=False)
    price = fr.get_fill_price(config.contract_id)
    assert price == 116.875
    assert calls["n"] >= 3
