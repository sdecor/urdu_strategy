# Types d’ordre API
ORDER_TYPE = {
    "Limit": 1,
    "Market": 2,
    "Stop": 4,
    "TrailingStop": 5,
    "JoinBid": 6,
    "JoinAsk": 7,
}

def map_position_to_side(position: int) -> int | None:
    """
    Mapping doc ProjectX: side = 0 (buy/Bid), 1 (sell/Ask)
    position  1 -> BUY (0)
    position -1 -> SELL (1)
    position  0 -> None (flatten ne passe pas par place_order)
    """
    if position == 1:
        return 0
    if position == -1:
        return 1
    return None
