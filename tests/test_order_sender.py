# tests/test_order_sender.py
from orders.order_sender import OrderSender


class EngineOK:
    def __init__(self):
        self.calls = []

    def place_order(self, payload):
        self.calls.append(payload)
        return {"success": True, "orderId": 1510001111, "errorCode": 0, "errorMessage": None}


class EngineFail:
    def place_order(self, payload):
        raise RuntimeError("boom")


def test_order_sender_success():
    eng = EngineOK()
    s = OrderSender(eng, logging_enabled=False)
    res = s.send({"foo": "bar"}, tag="TEST")
    assert res["success"] is True
    assert res["order_id"] == 1510001111
    assert res["error_code"] == 0
    assert res["error_message"] is None


def test_order_sender_exception():
    eng = EngineFail()
    s = OrderSender(eng, logging_enabled=False)
    res = s.send({"x": 1})
    assert res["success"] is False
    assert "exception" in (res["error_message"] or "").lower()
# tests/test_order_sender.py
from orders.order_sender import OrderSender


class EngineOK:
    def __init__(self):
        self.calls = []

    def place_order(self, payload):
        self.calls.append(payload)
        return {"success": True, "orderId": 1510001111, "errorCode": 0, "errorMessage": None}


class EngineFail:
    def place_order(self, payload):
        raise RuntimeError("boom")


def test_order_sender_success():
    eng = EngineOK()
    s = OrderSender(eng, logging_enabled=False)
    res = s.send({"foo": "bar"}, tag="TEST")
    assert res["success"] is True
    assert res["order_id"] == 1510001111
    assert res["error_code"] == 0
    assert res["error_message"] is None


def test_order_sender_exception():
    eng = EngineFail()
    s = OrderSender(eng, logging_enabled=False)
    res = s.send({"x": 1})
    assert res["success"] is False
    assert "exception" in (res["error_message"] or "").lower()
