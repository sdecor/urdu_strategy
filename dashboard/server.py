import unittest
from decimal import Decimal

from strategy.tp_manager import TPManager
from utils.config_loader import Config
from utils.price_math import parse_tick_size, add_ticks, round_to_tick


class TestTPManager(unittest.TestCase):
    def setUp(self):
        # Charge la configuration réelle (config.yaml + .env)
        self.config = Config()
        self.tp_manager = TPManager(self.config)

        # Récupère le contract_id depuis la config
        self.contract_id = getattr(self.config, "contract_id", None)
        if not self.contract_id:
            # Si aucun contract_id global n'est défini, tente de prendre le premier contrat défini
            contracts = getattr(self.config, "contracts", {}) or {}
            self.contract_id = next(iter(contracts.keys()), None)

        if not self.contract_id:
            self.skipTest("Aucun contract_id défini dans la configuration (config.contract_id ou contracts.*).")

        # Vérifie la présence du tick_size pour le contrat
        contracts = getattr(self.config, "contracts", {}) or {}
        if self.contract_id not in contracts:
            self.skipTest(f"Contrat '{self.contract_id}' absent de config.contracts.")

        self.tick_size_str = contracts[self.contract_id].get("tick_size")
        if not self.tick_size_str:
            self.skipTest(f"tick_size manquant pour le contrat '{self.contract_id}' dans config.contracts.")

        # Récupère les paramètres de stratégie
        strategy = getattr(self.config, "strategy", {}) or {}
        tp_cfg = strategy.get("tp", {}) or {}
        if "ticks" not in tp_cfg:
            self.skipTest("strategy.tp.ticks manquant dans la configuration.")

        self.ticks = int(tp_cfg["ticks"])
        self.size = int(getattr(self.config, "default_quantity", tp_cfg.get("default_quantity", 1)))

        # Compte & autres
        self.account_id = getattr(self.config, "account_id", None)
        if not self.account_id:
            self.skipTest("TOPSTEPX_ACCOUNT_ID manquant dans .env / Config.")

        # Convertit le tick_size en Decimal
        self.tick_size = parse_tick_size(self.tick_size_str)

    def test_long_tp_calculation(self):
        # Prix d'exécution simulé (valeur arbitraire de test)
        fill_price = Decimal("117.0")
        payload = self.tp_manager.build_tp_order_payload(
            account_id=int(self.account_id),
            contract_id=self.contract_id,
            entry_side=0,          # long
            size=self.size,
            fill_price=fill_price,
            linked_order_id=999
        )

        # Expectation calculée à partir de la config (pas de hardcode)
        expected_tp = round_to_tick(
            add_ticks(fill_price, self.ticks, self.tick_size, entry_side=0),
            self.tick_size
        )
        self.assertEqual(Decimal(str(payload["limitPrice"])), expected_tp)

    def test_short_tp_calculation(self):
        fill_price = Decimal("117.0")
        payload = self.tp_manager.build_tp_order_payload(
            account_id=int(self.account_id),
            contract_id=self.contract_id,
            entry_side=1,          # short
            size=self.size,
            fill_price=fill_price,
            linked_order_id=1000
        )

        expected_tp = round_to_tick(
            add_ticks(fill_price, self.ticks, self.tick_size, entry_side=1),
            self.tick_size
        )
        self.assertEqual(Decimal(str(payload["limitPrice"])), expected_tp)


if __name__ == "__main__":
    unittest.main()
