# utils/price_math.py
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Précision suffisante pour les prix de futures
getcontext().prec = 12

def parse_tick_size(value: str) -> Decimal:
    """
    Accepte '1/32', '0.03125', '0,03125' (virgule acceptée) et retourne un Decimal positif.
    """
    s = str(value).strip().replace(",", ".")
    if "/" in s:
        num, den = s.split("/", 1)
        num = Decimal(num.strip())
        den = Decimal(den.strip())
        if den == 0:
            raise ValueError("tick_size fraction denominator cannot be zero")
        return (num / den).copy_abs()
    d = Decimal(s)
    if d <= 0:
        raise ValueError("tick_size must be > 0")
    return d

def add_ticks(price: Decimal, ticks: int, tick_size: Decimal, entry_side: int) -> Decimal:
    """
    Calcule le TP à partir du prix d'exécution.
    entry_side: 0 = Buy (long), 1 = Sell (short)
    - Long  -> TP = price + ticks * tick_size
    - Short -> TP = price - ticks * tick_size
    """
    direction = 1 if entry_side == 0 else -1
    return price + (tick_size * Decimal(ticks * direction))

def round_to_tick(price: Decimal, tick_size: Decimal) -> Decimal:
    """
    Aligne un prix sur la grille des ticks (arrondi au multiple le plus proche).
    """
    q = (price / tick_size).to_integral_value(rounding=ROUND_HALF_UP)
    return (q * tick_size).normalize()
