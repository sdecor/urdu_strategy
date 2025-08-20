from typing import Iterable, List, Optional
from ..models.order import Order, OrderSide
from ..models.position import Position, PositionSide
from ..models.trade_state import TradeState
from .topstepx_client import TopstepXClient
from .lot_sizing import LotSizing


class ExecutionService:
    def __init__(self, client: TopstepXClient, lot_sizing: LotSizing, unique_trade_at_a_time: bool = True) -> None:
        self._client = client
        self._lots = lot_sizing
        self._unique = unique_trade_at_a_time

    def _apply_fill(self, state: TradeState, order: Order) -> None:
        pos = state.get_position(order.instrument)
        if order.side == OrderSide.BUY:
            if pos.side == PositionSide.SHORT:
                close_qty = min(pos.qty, order.qty)
                pos.qty -= close_qty
                if pos.qty == 0:
                    pos.side = PositionSide.FLAT
                remaining = order.qty - close_qty
                if remaining > 0:
                    if pos.side in (PositionSide.FLAT, PositionSide.LONG):
                        pos.side = PositionSide.LONG
                        pos.qty += remaining
            else:
                pos.side = PositionSide.LONG
                pos.qty += order.qty
        else:
            if pos.side == PositionSide.LONG:
                close_qty = min(pos.qty, order.qty)
                pos.qty -= close_qty
                if pos.qty == 0:
                    pos.side = PositionSide.FLAT
                remaining = order.qty - close_qty
                if remaining > 0:
                    if pos.side in (PositionSide.FLAT, PositionSide.SHORT):
                        pos.side = PositionSide.SHORT
                        pos.qty += remaining
            else:
                pos.side = PositionSide.SHORT
                pos.qty += order.qty
        state.set_position(pos)

    def execute_orders(self, state: TradeState, orders: Iterable[Order]) -> List[Order]:
        executed: List[Order] = []
        for o in orders:
            ok, _ = self._client.place_order(instrument=o.instrument, side=o.side.value, qty=o.qty, order_type=o.type.value, client_tag=o.client_tag or o.id)
            if ok:
                self._apply_fill(state, o)
                executed.append(o)
            else:
                break
        return executed

    def close_all(self, state: TradeState) -> List[Order]:
        placed: List[Order] = []
        for instr, pos in list(state.positions.items()):
            if pos.side == PositionSide.FLAT or pos.qty <= 0:
                continue
            if pos.side == PositionSide.LONG:
                o = Order.create(instr, OrderSide.SELL, pos.qty, client_tag="risk_flat_all")
            else:
                o = Order.create(instr, OrderSide.BUY, pos.qty, client_tag="risk_flat_all")
            ok, _ = self._client.place_order(instrument=o.instrument, side=o.side.value, qty=o.qty, order_type=o.type.value, client_tag=o.client_tag or o.id)
            if ok:
                self._apply_fill(state, o)
                placed.append(o)
        return placed

    def execute_signal_orders(self, state: TradeState, orders: Iterable[Order]) -> List[Order]:
        if self._unique:
            ok_open, _ = self._client.search_open_orders()
            if not ok_open:
                pass
        return self.execute_orders(state, orders)
