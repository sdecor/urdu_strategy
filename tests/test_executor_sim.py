# tests/test_executor.py
from decimal import Decimal
import math

from trading.executor import TradeExecutor


def _find_calls_of(calls, name):
    return [p for (n, p) in calls if n == name]


def test_market_then_tp_simulation(config, simulator_spy):
    """
    Vérifie que:
      - un MARKET est envoyé
      - un LIMIT TP est envoyé ensuite avec le bon side/size/limitPrice
    """
    ex = TradeExecutor(config)
    ok = ex.place_market(instrument="UB1!", side=0, size=1)  # long
    assert ok is True

    calls = simulator_spy
    place_calls = _find_calls_of(calls, "place_order")
    # 1 MARKET + 1 TP LIMIT
    assert len(place_calls) == 2

    market, tp = place_calls[0], place_calls[1]

    # MARKET
    assert market["type"] == 2
    assert market["side"] == 0
    assert market["size"] == 1
    assert market["contractId"] == config.contract_id
    assert market["accountId"] == config.account_id

    # TP LIMIT (pour un long: side doit être 1 = sell)
    assert tp["type"] == 1
    assert tp["side"] == 1
    assert tp["size"] == 1

    # prix attendu: 117.0 + 4 * 1/32 = 117.125
    expected = Decimal("117.125")
    got = Decimal(str(tp["limitPrice"]))
    assert got == expected


def test_schedule_A_total_tp(config, simulator_spy):
    """
    Stratégie A: tout au TP
    """
    ex = TradeExecutor(config)

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

    ok = ex.place_market_with_schedule(schedule, side=0)  # long
    assert ok is True

    place_calls = [p for (n, p) in simulator_spy if n == "place_order"]
    assert len(place_calls) == 2  # 1 MARKET (3) + 1 TP LIMIT (3)

    market, tp = place_calls[-2], place_calls[-1]
    assert market["size"] == 3
    assert tp["size"] == 3

    # prix TP: 117 + 4 * 1/32 = 117.125
    assert Decimal(str(tp["limitPrice"])) == Decimal("117.125")


def test_schedule_B_partial_tp_with_carry(config, simulator_spy):
    """
    Stratégie B: TP partiel + carry
    """
    ex = TradeExecutor(config)

    schedule = {
        "id": "day",
        "strategy": {
            "type": "B",
            "total_lots": 5,
            "tp_ticks": 4,
            "tp_lots": 2,
            "carry_remaining": True,
            "flatten_at_end": False,
        }
    }

    ok = ex.place_market_with_schedule(schedule, side=1)  # short
    assert ok is True

    place_calls = [p for (n, p) in simulator_spy if n == "place_order"]
    assert len(place_calls) >= 2

    market, tp = place_calls[-2], place_calls[-1]
    # MARKET short 5 lots, TP LIMIT 2 lots (buy-to-cover)
    assert market["side"] == 1
    assert market["size"] == 5
    assert tp["side"] == 0
    assert tp["size"] == 2

    # prix TP: 117 - 4 * 1/32 = 116.875
    assert str(tp["limitPrice"]) == "116.875"
