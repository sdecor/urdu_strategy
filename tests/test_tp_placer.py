# tests/test_tp_placer.py
from strategy.tp_placer import TPPlacer


class DummyFillResolver:
    def __init__(self, price):
        self.price = price
    def get_fill_price(self, _):
        return self.price


class DummyTPManager:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
    def build_tp_order_payload(self, **kwargs):
        self.calls += 1
        return dict(self.payload)


class DummyOrderSender:
    def __init__(self, success=True):
        self.success = success
        self.sent = []
    def send(self, payload, tag=""):
        self.sent.append((tag, dict(payload)))
        return {"success": self.success, "order_id": 1510099999}


def test_tp_placer_success(config):
    tp_payload = {
        "accountId": config.account_id,
        "contractId": config.contract_id,
        "type": 1, "side": 1, "size": 2, "limitPrice": 117.125
    }
    tp_manager = DummyTPManager(tp_payload)
    fr = DummyFillResolver(117.0)
    sender = DummyOrderSender(success=True)

    placer = TPPlacer(tp_manager, fr, sender, logging_enabled=False)
    ok = placer.place_tp_after_entry(
        account_id=config.account_id,
        contract_id=config.contract_id,
        entry_order_id=1510000001,
        entry_side=0,
        size=2,
        override_ticks=4
    )
    assert ok is True
    assert tp_manager.calls == 1
    assert len(sender.sent) == 1
    assert sender.sent[0][1]["type"] == 1


def test_tp_placer_no_fill(config):
    class NoFillResolver:
        def get_fill_price(self, _): return None

    tp_manager = DummyTPManager({"type": 1})
    sender = DummyOrderSender(success=True)

    placer = TPPlacer(tp_manager, NoFillResolver(), sender, logging_enabled=False)
    ok = placer.place_tp_after_entry(
        account_id=config.account_id,
        contract_id=config.contract_id,
        entry_order_id=1,
        entry_side=0,
        size=1
    )
    assert ok is False
    # no send when no fill
    assert len(sender.sent) == 0
