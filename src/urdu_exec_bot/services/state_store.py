from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, Union


# ----------------------------- paths & settings -----------------------------

def _project_root() -> Path:
    # src/urdu_exec_bot/services/state_store.py -> project root is parents[3]
    return Path(__file__).resolve().parents[3]


def _load_settings(settings_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Charge config/settings.yaml (ou le chemin forcé).
    On évite des dépendances externes pour rester robuste au boot.
    """
    import yaml  # lazy import

    if settings_path:
        sp = Path(settings_path)
    else:
        default_path = _project_root() / "config" / "settings.yaml"
        sp = Path(os.environ.get("SETTINGS_PATH", str(default_path)))

    try:
        if sp.exists():
            with sp.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception:
        pass
    return {}


def _resolve_state_path(settings: Dict[str, Any]) -> Path:
    p = (
        (settings.get("paths", {}) or {})
        .get("state", {})
        .get("trade_state")
    )
    if p:
        return Path(p)
    # défaut
    return _project_root() / "state" / "trade_state.json"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ----------------------------- default & validate -----------------------------

def _today_local_iso(date_tz: timezone | None = None) -> str:
    return datetime.now(tz=date_tz).date().isoformat()


def _default_state() -> Dict[str, Any]:
    return {
        "positions": {},                         # { "UB1!": {"side": "LONG"/"SHORT"/"FLAT", "size": 0}, ... }
        "pnl": {"today": 0.0, "date": _today_local_iso()},
        "evaluation": {"halted": False, "halt_reason": ""},  # stop trading si plafond atteint
        "meta": {"version": 1},
    }


def _merge_defaults(state: Dict[str, Any]) -> Dict[str, Any]:
    d = _default_state()
    state = state if isinstance(state, dict) else {}
    state.setdefault("positions", d["positions"])
    state.setdefault("pnl", {})
    state["pnl"].setdefault("today", 0.0)
    state["pnl"].setdefault("date", d["pnl"]["date"])
    state.setdefault("evaluation", {})
    state["evaluation"].setdefault("halted", False)
    state["evaluation"].setdefault("halt_reason", "")
    state.setdefault("meta", {})
    state["meta"].setdefault("version", 1)
    return state


# ----------------------------- module-level API -----------------------------

def load(settings_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Charge l'état du fichier JSON.
    - Si le fichier est absent ou VIDE → crée et retourne un état par défaut.
    - Si JSON invalide → sauvegarde un .bak et réinitialise avec l'état par défaut.
    - Remplit les champs manquants si nécessaire.
    """
    settings = _load_settings(settings_path)
    path = _resolve_state_path(settings)
    _ensure_parent(path)

    if not path.exists() or path.stat().st_size == 0:
        state = _default_state()
        save(state, settings_path=settings_path)
        return state

    try:
        with path.open("r", encoding="utf-8") as f:
            data = f.read().strip()
        if not data:
            state = _default_state()
            save(state, settings_path=settings_path)
            return state

        parsed = json.loads(data)
        return _merge_defaults(parsed)

    except Exception:
        # Fichier corrompu: sauvegarder une copie .bak horodatée puis réinitialiser
        try:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            bak = path.with_suffix(path.suffix + f".bak-{ts}")
            try:
                with path.open("rb") as fin, bak.open("wb") as fout:
                    fout.write(fin.read())
            except Exception:
                try:
                    path.rename(bak)
                except Exception:
                    pass
        finally:
            state = _default_state()
            save(state, settings_path=settings_path)
            return state


def save(state: Dict[str, Any], settings_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """
    Sauvegarde atomique de l'état (write + replace).
    Retourne (ok, message).
    """
    settings = _load_settings(settings_path)
    path = _resolve_state_path(settings)
    _ensure_parent(path)

    state = _merge_defaults(state)

    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
        return True, str(path)
    except Exception as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return False, f"write_error: {e}"


def reset(settings_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """
    Réinitialise l'état à la valeur par défaut et l’enregistre.
    """
    return save(_default_state(), settings_path=settings_path)


# ----------------------------- class wrapper (compat) -----------------------------

class StateStore:
    """
    Compatibilité / façade objet.
    Permet d'utiliser une API orientée objet tout en réutilisant les fonctions ci-dessus.
    """

    def __init__(self, settings_path: Optional[Union[str, Path]] = None) -> None:
        self._settings_path = Path(settings_path) if settings_path else None

    def load(self) -> Dict[str, Any]:
        return load(settings_path=self._settings_path)

    def save(self, state: Dict[str, Any]) -> Tuple[bool, str]:
        return save(state, settings_path=self._settings_path)

    def reset(self) -> Tuple[bool, str]:
        return reset(settings_path=self._settings_path)

    # Méthodes de classe pour un usage direct sans instance
    @classmethod
    def load_static(cls, settings_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        return load(settings_path=settings_path)

    @classmethod
    def save_static(cls, state: Dict[str, Any], settings_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
        return save(state, settings_path=settings_path)

    @classmethod
    def reset_static(cls, settings_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
        return reset(settings_path=settings_path)
