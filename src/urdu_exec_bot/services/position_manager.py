from typing import List
from ..models.position import Position, PositionSide
from ..models.order import Order, OrderSide, OrderType


class PositionManager:
    def compute_orders(self, current: Position, target_side: PositionSide, lot_qty: int) -> List[Order]:
        orders: List[Order] = []
        if target_side == PositionSide.FLAT:
            if current.side == PositionSide.LONG and current.qty > 0:
                orders.append(Order.create(current.instrument, OrderSide.SELL, current.qty, OrderType.MARKET, client_tag="close_long"))
            elif current.side == PositionSide.SHORT and current.qty > 0:
                orders.append(Order.create(current.instrument, OrderSide.BUY, current.qty, OrderType.MARKET, client_tag="close_short"))
            return orders

        if current.side == PositionSide.FLAT:
            if target_side == PositionSide.LONG:
                orders.append(Order.create(current.instrument, OrderSide.BUY, lot_qty, OrderType.MARKET, client_tag="open_long"))
            elif target_side == PositionSide.SHORT:
                orders.append(Order.create(current.instrument, OrderSide.SELL, lot_qty, OrderType.MARKET, client_tag="open_short"))
            return orders

        if current.side == PositionSide.LONG and target_side == PositionSide.SHORT:
            if current.qty > 0:
                orders.append(Order.create(current.instrument, OrderSide.SELL, current.qty, OrderType.MARKET, client_tag="close_long"))
            orders.append(Order.create(current.instrument, OrderSide.SELL, lot_qty, OrderType.MARKET, client_tag="open_short"))
            return orders

        if current.side == PositionSide.SHORT and target_side == PositionSide.LONG:
            if current.qty > 0:
                orders.append(Order.create(current.instrument, OrderSide.BUY, current.qty, OrderType.MARKET, client_tag="close_short"))
            orders.append(Order.create(current.instrument, OrderSide.BUY, lot_qty, OrderType.MARKET, client_tag="open_long"))
            return orders

        if current.side == target_side:
            return []

        return orders
