import logging
import logging.config
from pathlib import Path
import os
import yaml


def setup_logging(settings_path: str) -> None:
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}
    logging_cfg_path = settings.get("config_files", {}).get("logging")
    if not logging_cfg_path:
        logging.basicConfig(level=logging.INFO)
        return
    path = Path(logging_cfg_path)
    if not path.is_absolute():
        root = Path(settings_path).resolve().parents[1]
        path = (root / logging_cfg_path).resolve()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        logging.config.dictConfig(cfg)
    else:
        logging.basicConfig(level=logging.INFO)
