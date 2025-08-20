from typing import Optional
from ..models.trade_state import TradeState


class PnLTracker:
    def __init__(self, state: TradeState) -> None:
        self._state = state

    def add(self, amount: float) -> float:
        self._state.pnl_day = float(self._state.pnl_day) + float(amount)
        return self._state.pnl_day

    def set(self, amount: float) -> float:
        self._state.pnl_day = float(amount)
        return self._state.pnl_day

    def get(self) -> float:
        return float(self._state.pnl_day)

    def attach(self, state: Optional[TradeState] = None) -> None:
        if state is not None:
            self._state = state
