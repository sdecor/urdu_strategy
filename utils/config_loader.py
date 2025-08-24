import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self, config_path="config/config.yaml"):
        load_dotenv()

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.api_key = os.getenv("TOPSTEPX_API_KEY")
        self.base_url = os.getenv("TOPSTEPX_BASE_URL")
        self.username = os.getenv("TOPSTEPX_USERNAME")
        self.account_id = os.getenv("TOPSTEPX_ACCOUNT_ID")

        self.mode = self.config.get("mode", "simulation")
        self.poll_interval_seconds = self.config.get("poll_interval_seconds", 1)
        self.dashboard = self.config.get("dashboard", {})
        self.api_endpoints = self.config.get("api_endpoints", {})
        self.logging_enabled = self.config.get("logging", True)
        self.log_file = self.config.get("log_file", "urdu_bot.log")
        self.contract_id = self.config.get("contract_id")
        self.default_quantity = self.config.get("default_quantity", 1)
        self.contract_id = self.config.get("contract_id")
        self.default_quantity = self.config.get("default_quantity", 1)
        self.default_order_type = self.config.get("default_order_type", 2)
