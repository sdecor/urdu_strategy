# trading/simulator.py
from __future__ import annotations

from typing import Dict, Any, List, Optional
from utils.logger import log


class TradeSimulator:
    """
    Simulateur minimal pour les tests/intégration:
    - place_order(payload) -> renvoie {"success": True, "orderId": int}
    - get_open_positions() -> liste des positions "ouvertes" (optionnel pour tests)
    - flatten_all() -> reset des positions
    Notes:
      * On ne simule pas les prix de marché; pour les tests TP, tu peux monkeypatcher
        get_open_positions() pour retourner un averagePrice (comme dans ton test).
      * Néanmoins, on maintient un petit état interne si tu veux l’utiliser sans monkeypatch.
    """

    def __init__(self, config, logging_enabled: Optional[bool] = None):
        self.config = config
        self.logging_enabled = logging_enabled if logging_enabled is not None else True

        self._next_order_id = 1
        self._orders: List[Dict[str, Any]] = []
        # positions par contractId: {"size": int, "averagePrice": float}
        self._positions: Dict[str, Dict[str, Any]] = {}

    # ------ API utilisée par TradeExecutor ------
    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simule l'acceptation immédiate des ordres MARKET (type=2) et LIMIT (type=1).
        - MARKET: ouvre/augmente une position à un prix "fake".
        - LIMIT (TP): on l’accepte et on le stocke; pas d’exécution auto (simple).
        """
        order_id = self._next_order_id
        self._next_order_id += 1

        # Stocke l'ordre pour debug
        rec = dict(payload)
        rec["orderId"] = order_id
        self._orders.append(rec)

        # Gestion simplifiée des positions si MARKET (type=2)
        typ = int(payload.get("type", 0))
        side = int(payload.get("side", 0))        # 0=buy, 1=sell
        size = int(payload.get("size", 0))
        contract_id = payload.get("contractId")

        if typ == 2 and contract_id and size > 0:
            # Détermine un prix d'exé fictif si personne ne monkeypatch get_open_positions
            # (pour éviter de "hardcoder", on peut lire une valeur depuis la config si présente,
            # sinon valeur par défaut neutre)
            default_fill_price = 100.0
            try:
                # Si tu définis par ex. config.simulator.default_fill_price dans config.yaml
                default_fill_price = float(self.config.config.get("simulator", {}).get("default_fill_price", 100.0))
            except Exception:
                pass

            pos = self._positions.get(contract_id)
            if pos is None:
                # ouvre une nouvelle position: averagePrice = default_fill_price
                signed_size = size if side == 0 else -size
                self._positions[contract_id] = {
                    "size": signed_size,
                    "averagePrice": default_fill_price
                }
            else:
                # ajuste la taille; on laisse averagePrice identique pour simplifier
                signed_size = size if side == 0 else -size
                pos["size"] = pos.get("size", 0) + signed_size

        log(f"[SIM] place_order accepted -> {rec}", self.logging_enabled)
        return {"success": True, "orderId": order_id, "errorCode": 0, "errorMessage": None}

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Retourne les positions ouvertes sous la forme de l’API TopstepX:
        [{"contractId": str, "size": int, "averagePrice": float}, ...]
        """
        out = []
        for cid, p in self._positions.items():
            if p.get("size"):
                out.append({
                    "contractId": cid,
                    "size": p["size"],
                    "averagePrice": p.get("averagePrice", None)
                })
        log(f"[SIM] get_open_positions -> {out}", self.logging_enabled)
        return out

    def flatten_all(self) -> None:
        """
        Réinitialise toutes les positions à 0 (fermeture).
        """
        for cid in list(self._positions.keys()):
            self._positions[cid]["size"] = 0
        log("[SIM] flatten_all -> all positions set to 0", self.logging_enabled)
