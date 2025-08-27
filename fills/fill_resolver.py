# fills/fill_resolver.py
from __future__ import annotations

import time
import random
from typing import Optional, Dict, Any, List

from utils.logger import log


class FillResolver:
    """
    Récupère un 'fill price' exploitable après un ordre d'entrée, via la/les sources disponibles.
    Implémentation par défaut: poll sur get_open_positions() et lit averagePrice.

    Paramètres (issus de la config si présents):
      config.fills:
        retries: int = 10
        delay_seconds: float = 0.2
        jitter_seconds: float = 0.05
        require_size_nonzero: bool = True   # vérifie qu'une position non-nulle existe
        source: str = "positions"           # réserve pour futures sources ("orders", "exec_reports")

    Exemple config.yaml:
      fills:
        retries: 12
        delay_seconds: 0.25
        jitter_seconds: 0.05
        require_size_nonzero: true
        source: "positions"
    """

    def __init__(self, engine, config, logging_enabled: bool = True):
        """
        Args:
            engine: objet avec .get_open_positions() (SimEngine ou LiveEngine)
            config: Config (config_loader.Config)
        """
        self.engine = engine
        self.config = config
        self.logging_enabled = logging_enabled

        fills_cfg: Dict[str, Any] = getattr(config, "config", {}).get("fills", {}) or {}
        self.retries: int = int(fills_cfg.get("retries", 10))
        self.delay_seconds: float = float(fills_cfg.get("delay_seconds", 0.2))
        self.jitter_seconds: float = float(fills_cfg.get("jitter_seconds", 0.05))
        self.require_size_nonzero: bool = bool(fills_cfg.get("require_size_nonzero", True))
        self.source: str = str(fills_cfg.get("source", "positions")).lower()

    # -------- Public API --------
    def get_fill_price(self, contract_id: str) -> Optional[float]:
        """
        Retourne un prix d'exécution (float) si trouvé, sinon None.
        Actuellement, utilise la source 'positions' par polling.
        """
        if self.source == "positions":
            return self._from_positions(contract_id)

        # Placeholders pour futures sources (si tu ajoutes des endpoints d'exécutions)
        # elif self.source == "orders":
        #     return self._from_orders(contract_id)
        # elif self.source == "exec_reports":
        #     return self._from_exec_reports(contract_id)

        # fallback
        return self._from_positions(contract_id)

    # -------- Sources internes --------
    def _from_positions(self, contract_id: str) -> Optional[float]:
        """
        Poll get_open_positions() jusqu'à trouver averagePrice pour le contrat demandé.
        """
        if not hasattr(self.engine, "get_open_positions"):
            log("[FILL] Engine ne supporte pas get_open_positions()", self.logging_enabled)
            return None

        for attempt in range(1, self.retries + 1):
            try:
                positions: List[Dict[str, Any]] = self.engine.get_open_positions() or []
                # format attendu TopstepX: {"contractId": "...", "size": int, "averagePrice": float}
                for p in positions:
                    if p.get("contractId") == contract_id:
                        size_ok = (not self.require_size_nonzero) or bool(p.get("size"))
                        avg = p.get("averagePrice")
                        if size_ok and avg is not None:
                            log(f"[FILL] averagePrice trouvé (attempt={attempt}) -> {avg}", self.logging_enabled)
                            return float(avg)
            except Exception as e:
                log(f"[FILL] Exception get_open_positions: {e}", self.logging_enabled)

            # Attente avec jitter
            sleep_for = self.delay_seconds + random.uniform(0, self.jitter_seconds)
            time.sleep(sleep_for)

        log("[FILL] Prix d'exécution introuvable après polling.", self.logging_enabled)
        return None

    # def _from_orders(self, contract_id: str) -> Optional[float]:
    #     """
    #     TODO: Ex: interroger order_search / order executions si exposés.
    #     """
    #     return None

    # def _from_exec_reports(self, contract_id: str) -> Optional[float]:
    #     """
    #     TODO: Ex: flux temps réel d'executions si disponible (websocket/SignalR).
    #     """
    #     return None
