from typing import List
from ..models.signal import Signal, SignalAction
from ..models.position import PositionSide
from .position_manager import PositionManager
from .lot_sizing import LotSizing
from ..models.order import Order


class StrategyEngine:
    def __init__(self, lot_sizing: LotSizing, position_manager: PositionManager) -> None:
        self._lots = lot_sizing
        self._pm = position_manager

    def decide_orders(self, signal: Signal, current_position, lot_override: int = 0) -> List[Order]:
        action = signal.action
        instrument = signal.instrument
        lot_qty = lot_override if lot_override > 0 else self._lots.get_qty(instrument)
        if action == SignalAction.LONG:
            target = PositionSide.LONG
        elif action == SignalAction.SHORT:
            target = PositionSide.SHORT
        else:
            if current_position.side == PositionSide.LONG:
                target = PositionSide.SHORT
            elif current_position.side == PositionSide.SHORT:
                target = PositionSide.LONG
            else:
                return []
        return self._pm.compute_orders(current_position, target, lot_qty)
