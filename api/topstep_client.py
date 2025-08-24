from api.http_base import HttpBase
from api.orders import OrdersService
from api.accounts import AccountsService
from utils.logger import log


class TopstepXClient:
    def __init__(
        self,
        api_key,
        base_url,
        username,
        account_id,
        endpoints=None,
        logging_enabled=True,
        contract_id=None,
        default_order_type=2
    ):
        self.http = HttpBase(
            api_key=api_key,
            base_url=base_url,
            username=username,
            account_id=account_id,
            endpoints=endpoints,
            logging_enabled=logging_enabled
        )
        self.orders = OrdersService(
            http_base=self.http,
            contract_id=contract_id,
            default_order_type=default_order_type
        )
        self.accounts = AccountsService(http_base=self.http)
        self.contract_id = contract_id
        self.logging_enabled = logging_enabled

    def execute_trade(self, instrument: str, position: int, size: int = 1):
        return self.orders.place_order(position=position, size=size)

    def place_order(self, **kwargs):
        return self.orders.place_order(**kwargs)

    def cancel_order(self, order_id: int):
        return self.orders.cancel_order(order_id)

    def get_open_positions(self):
        return self.accounts.get_open_positions()

    def get_working_orders(self):
        return self.accounts.get_working_orders()

    # 🆕 Flatten all (pour le contrat configuré)
    def flatten_all(self):
        """
        Ferme toutes les positions ouvertes du contrat configuré (contract_id)
        en envoyant un ordre au marché inverse de taille équivalente.
        """
        data = self.get_open_positions()
        if not data:
            log("[FLATTEN] Aucune donnée de positions reçue.", self.logging_enabled)
            return

        positions = self._extract_positions_list(data)
        if not positions:
            log("[FLATTEN] Aucune position ouverte détectée.", self.logging_enabled)
            return

        count = 0
        for pos in positions:
            c_id = pos.get("contractId") or pos.get("contractID") or pos.get("contract_id")
            if self.contract_id and c_id and c_id != self.contract_id:
                continue  # on ne traite que le contrat de la config

            # champs possibles: side (0/1) et size (int)
            side = pos.get("side")
            size = pos.get("size") or pos.get("quantity") or pos.get("qty")

            try:
                size = int(size)
            except Exception:
                size = None

            if side is None or not size:
                log(f"[FLATTEN] Position ignorée (incomplète): {pos}", self.logging_enabled)
                continue

            # side 0 = long -> on vend (position -1), side 1 = short -> on achète (position +1)
            reverse_position = -1 if side == 0 else 1
            log(f"[FLATTEN] Fermeture position {c_id} side={side} size={size} -> ordre inverse {reverse_position}", self.logging_enabled)
            self.execute_trade(instrument="N/A", position=reverse_position, size=size)
            count += 1

        if count == 0:
            log("[FLATTEN] Rien à fermer pour ce contrat.", self.logging_enabled)
        else:
            log(f"[FLATTEN] Demandes de fermeture envoyées: {count}", self.logging_enabled)

    @staticmethod
    def _extract_positions_list(data):
        """
        Essaie d'extraire une liste de positions depuis la réponse API.
        On tolère quelques formats courants: {'positions': [...]}, {'openPositions': [...]}, ou directement une liste.
        """
        if isinstance(data, dict):
            for key in ("positions", "openPositions", "items", "data"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        if isinstance(data, list):
            return data
        return []
