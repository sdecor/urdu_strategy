from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _fallback_config() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,  # remplace tout handler existant pour garantir l'horodatage
    )


def setup_logging(config_path: Optional[str | Path]) -> None:
    """
    Charge une config YAML (dictConfig). En cas d'échec ou d'absence,
    applique une configuration par défaut avec horodatage.
    """
    if not config_path:
        _fallback_config()
        return

    p = Path(config_path)
    if not p.exists():
        _fallback_config()
        return

    try:
        with p.open("r", encoding="utf-8") as f:
            cfg: Dict[str, Any] = yaml.safe_load(f) or {}
        if isinstance(cfg, dict) and cfg:
            logging.config.dictConfig(cfg)
            return
    except Exception:
        pass

    _fallback_config()
