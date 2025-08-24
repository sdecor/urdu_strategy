from utils.logger import log


class LotManager:
    def __init__(self, default_quantity=1, logging_enabled=True):
        self.default_quantity = default_quantity
        self.logging_enabled = logging_enabled

    def get_quantity(self, instrument: str, signal: dict, context: dict = None) -> int:
        """
        Détermine dynamiquement la quantité (lots) à trader pour un instrument.

        :param instrument: Nom de l'instrument (ex: "UB1!")
        :param signal: Signal brut (dict) contenant 'timestamp', 'position', etc.
        :param context: Contexte additionnel (ex: positions ouvertes, PnL, etc.)
        :return: Nombre de lots à trader (int)
        """
        # 🔧 Logique future : adapter selon instrument, contexte, signal...
        quantity = self.default_quantity

        log(f"[LOTS] Quantité calculée pour {instrument} : {quantity}", self.logging_enabled)
        return quantity
