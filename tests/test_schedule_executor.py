# tests/test_schedule_executor.py
from strategy.schedule_executor import ScheduleExecutor


class SpySender:
    def __init__(self, success=True):
        self.success = success
        self.sent = []
    def send(self, payload, tag=""):
        self.sent.append((tag, dict(payload)))
        if self.success:
            return {"success": True, "order_id": 1510100000}
        return {"success": False, "error_message": "fail"}


class SpyTPPlacer:
    def __init__(self):
        self.calls = []
    def place_tp_after_entry(self, **kwargs):
        self.calls.append(kwargs)
        return True


def test_schedule_exec_A_all_tp(config):
    # MARKET + TP for all lots
    sender = SpySender(success=True)
    se = ScheduleExecutor(
        config=config,
        order_builder=None,
        order_sender=sender,
        tp_placer=SpyTPPlacer(),
        logging_enabled=False
    )

    from orders.order_builder import OrderBuilder
    se.order_builder = OrderBuilder(config)

    schedule = {
        "id": "morning",
        "strategy": {
            "type": "A",
            "total_lots": 3,
            "tp_ticks": 4,
            "tp_lots": 3,
            "carry_remaining": False,
            "flatten_at_end": False,
        }
    }

    ok = se.execute(schedule, side=0)  # long
    assert ok is True

    # One MARKET + TP placer called once
    market_calls = [p for (tag, p) in sender.sent if tag == "MARKET"]
    assert len(market_calls) == 1

    market_payload = market_calls[0]
    assert market_payload["type"] == 2
    assert market_payload["size"] == 3
    assert market_payload["side"] == 0
