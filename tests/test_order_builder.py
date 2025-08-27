# tests/test_order_builder.py
import pytest
from orders.order_builder import OrderBuilder


def test_build_market_order_ok(config):
    b = OrderBuilder(config)
    p = b.build_market_order(
        side=0, size=2,
        account_id=config.account_id,
        contract_id=config.contract_id,
        order_type=2
    )
    assert p["type"] == 2
    assert p["side"] == 0
    assert p["size"] == 2
    assert p["accountId"] == config.account_id
    assert p["contractId"] == config.contract_id


def test_build_market_missing_contract_uses_config(config):
    b = OrderBuilder(config)
    p = b.build_market_order(
        side=1, size=1, account_id=config.account_id
    )
    assert p["contractId"] == config.contract_id


def test_build_market_invalid_size(config):
    b = OrderBuilder(config)
    with pytest.raises(ValueError):
        b.build_market_order(side=0, size=0)


def test_build_limit_order_ok(config):
    b = OrderBuilder(config)
    p = b.build_limit_order(
        side=1, size=3, limit_price=117.125,
        account_id=config.account_id,
        contract_id=config.contract_id,
        linked_order_id=999
    )
    assert p["type"] == 1
    assert p["side"] == 1
    assert p["size"] == 3
    assert p["limitPrice"] == 117.125
    assert p["linkedOrderId"] == 999
    assert p["accountId"] == config.account_id
    assert p["contractId"] == config.contract_id


def test_build_limit_requires_price(config):
    b = OrderBuilder(config)
    with pytest.raises(ValueError):
        b.build_limit_order(side=1, size=1, limit_price=None)
