import os
import yaml
from dotenv import load_dotenv


class Config:
    def __init__(self, config_path="config/config.yaml"):
        load_dotenv()

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f) or {}

        # .env (sensibles)
        self.api_key = os.getenv("TOPSTEPX_API_KEY")
        self.base_url = os.getenv("TOPSTEPX_BASE_URL")
        self.username = os.getenv("TOPSTEPX_USERNAME")
        self.account_id = os.getenv("TOPSTEPX_ACCOUNT_ID")

        # Général
        self.mode = self.config.get("mode", "simulation")
        self.poll_interval_seconds = self.config.get("poll_interval_seconds", 1)
        self.logging_enabled = self.config.get("logging", True)
        self.log_file = self.config.get("log_file", "logs/urdu_bot.log")

        # Blocs de config
        self.paths = self.config.get("paths", {}) or {}
        self.dashboard = self.config.get("dashboard", {}) or {}
        self.api_endpoints = self.config.get("api_endpoints", {}) or {}
        self.trading_hours = self.config.get("trading_hours", {}) or {}

        # Historique (garde pour compat)
        self.strategy = self.config.get("strategy", {}) or {}
        self.contracts = self.config.get("contracts", {}) or {}

        # Nouveaux champs (templates + schedules top-level)
        self.strategy_templates = self.config.get("strategy_templates", []) or []
        self.schedules = self.config.get("schedules", []) or []

        # Dérivés historiques (fallbacks)
        tp_cfg = self.strategy.get("tp", {}) or {}
        self.default_quantity = tp_cfg.get("default_quantity", 1)
        self.default_order_type = self.config.get("default_order_type", self.strategy.get("default_order_type", 2))

        # Contrat actif (si présent)
        self.contract_id = self.config.get("contract_id")
