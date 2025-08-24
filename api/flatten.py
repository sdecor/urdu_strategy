from utils.logger import log


class FlattenService:
    """
    Ferme toutes les positions du contrat configuré en envoyant des ordres inverses.
    Repose sur AccountsService (lecture) + OrdersService (place inverse).
    """
    def __init__(self, accounts_service, orders_service, contract_id: str, logging_enabled: bool = True):
        self.accounts = accounts_service
        self.orders = orders_service
        self.contract_id = contract_id
        self.logging_enabled = logging_enabled

    def flatten_all(self):
        data = self.accounts.get_open_positions()
        results = []
        if not data:
            log("[FLATTEN] Aucune donnée de positions reçue.", self.logging_enabled)
            return results

        positions = self._extract_positions_list(data)
        if not positions:
            log("[FLATTEN] Aucune position ouverte détectée.", self.logging_enabled)
            return results

        for pos in positions:
            c_id = pos.get("contractId") or pos.get("contractID") or pos.get("contract_id")
            if self.contract_id and c_id and c_id != self.contract_id:
                continue  # on limite au contrat configuré

            side = pos.get("side")  # 0 = long, 1 = short
            size = pos.get("size") or pos.get("quantity") or pos.get("qty")
            try:
                size = int(size)
            except Exception:
                size = None

            if side is None or not size:
                log(f"[FLATTEN] Position ignorée (incomplète): {pos}", self.logging_enabled)
                continue

            # ordre inverse : si long (0) -> SELL (position -1), si short (1) -> BUY (position +1)
            reverse_position = -1 if side == 0 else 1
            log(f"[FLATTEN] Fermeture {c_id} side={side} size={size} -> ordre inverse {reverse_position}", self.logging_enabled)
            res = self.orders.place_order(position=reverse_position, size=size)
            results.append(res)

        if not results:
            log("[FLATTEN] Rien à fermer pour ce contrat.", self.logging_enabled)
        else:
            log(f"[FLATTEN] Demandes de fermeture envoyées: {len(results)}", self.logging_enabled)
        return results

    @staticmethod
    def _extract_positions_list(data):
        if isinstance(data, dict):
            for key in ("positions", "openPositions", "items", "data"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        if isinstance(data, list):
            return data
        return []
