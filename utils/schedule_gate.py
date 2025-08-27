# utils/schedule_gate.py
from __future__ import annotations

import datetime
import json
import os
from typing import Dict, Optional, Tuple, Any, List


class FileSessionStorage:
    """
    Persistance JSON des compteurs d'entrées par schedule / par jour UTC.
    Clé: "YYYY-MM-DD:<schedule_id>" -> int
    """
    def __init__(self, path: str):
        self.path = path
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)

    def _load(self) -> Dict[str, int]:
        if not self.path or not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save(self, data: Dict[str, int]) -> None:
        if not self.path:
            return
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str) -> int:
        return int(self._load().get(key, 0))

    def set(self, key: str, value: int) -> None:
        data = self._load()
        data[key] = int(value)
        self._save(data)


def _parse_hhmm_utc(s: str) -> datetime.time:
    hh, mm = s.strip().split(":")
    return datetime.time(int(hh), int(mm), tzinfo=datetime.UTC)


class ScheduleGate:
    """
    Gère plusieurs fenêtres (schedules) avec quotas journaliers + stratégies par schedule.
    - schedules_config: liste de schedules (top-level "schedules" du YAML)
    - strategy_templates: liste de templates (top-level "strategy_templates")
    - résolution: si schedule["strategy"] est une string (ex: "A"), on injecte l'objet template correspondant.
                  la config du schedule a priorité si elle redéfinit un champ du template.
    """
    def __init__(
        self,
        schedules_config: List[Dict[str, Any]],
        storage: FileSessionStorage,
        logging_enabled: bool = True,
        strategy_templates: Optional[List[Dict[str, Any]]] = None,
    ):
        if not schedules_config:
            raise ValueError("ScheduleGate requires a non-empty 'schedules' list in config.yaml")

        # Indexe les templates par 'type'
        templates_index: Dict[str, Dict[str, Any]] = {}
        for t in (strategy_templates or []):
            ttype = t.get("type")
            if not ttype:
                continue
            templates_index[str(ttype)] = dict(t)  # shallow copy

        # Construit les schedules résolus
        self.schedules: Dict[str, Dict[str, Any]] = {}
        for sch in schedules_config:
            sid = sch["id"]
            start = _parse_hhmm_utc(sch["start_utc"])
            end = _parse_hhmm_utc(sch["end_utc"])
            max_trades = int(sch.get("max_trades", templates_index.get(sch.get("strategy"), {}).get("max_trades", 1)))

            # Résolution de la stratégie
            strat_ref = sch.get("strategy")
            if isinstance(strat_ref, str):
                if strat_ref not in templates_index:
                    raise ValueError(f"Unknown strategy template '{strat_ref}' for schedule '{sid}'")
                # base = template
                strategy_obj = dict(templates_index[strat_ref])
            elif isinstance(strat_ref, dict):
                strategy_obj = dict(strat_ref)
            else:
                strategy_obj = {}

            # Merge schedule overrides → prio au schedule si champs communs
            # (ici, on conserve strategy_obj tel quel, le schedule peut ajouter d'autres clés si besoin)
            self.schedules[sid] = {
                **sch,
                "start": start,
                "end": end,
                "max_trades": max_trades,
                "strategy": strategy_obj or None,
            }

        self.storage = storage
        self.logging_enabled = logging_enabled

    @staticmethod
    def _today_utc_str(now: Optional[datetime.datetime] = None) -> str:
        now = now or datetime.datetime.now(datetime.UTC)
        return now.date().isoformat()

    def current_schedule_id(self, now: Optional[datetime.datetime] = None) -> Optional[str]:
        t = (now or datetime.datetime.now(datetime.UTC)).time()
        for sid, sch in self.schedules.items():
            if sch["start"] <= t <= sch["end"]:
                return sid
        return None

    def get_schedule(self, schedule_id: str) -> Dict[str, Any]:
        return self.schedules[schedule_id]

    def can_enter(self, now: Optional[datetime.datetime] = None) -> Tuple[bool, Optional[str], int, int]:
        """
        Retourne (ok, schedule_id, used, max_allowed) pour la fenêtre courante.
        """
        sid = self.current_schedule_id(now)
        if not sid:
            return False, None, 0, 0
        today = self._today_utc_str(now)
        key = f"{today}:{sid}"
        used = self.storage.get(key)
        max_allowed = self.schedules[sid]["max_trades"]
        return (used < max_allowed), sid, used, max_allowed

    def mark_entry(self, schedule_id: str, now: Optional[datetime.datetime] = None) -> None:
        today = self._today_utc_str(now)
        key = f"{today}:{schedule_id}"
        used = self.storage.get(key)
        self.storage.set(key, used + 1)
