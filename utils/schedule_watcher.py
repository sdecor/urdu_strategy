# utils/schedule_watcher.py
from __future__ import annotations

import datetime
from typing import List, Dict, Any, Optional
from utils.logger import log


def _parse_hhmm_utc(s: str) -> datetime.time:
    hh, mm = s.strip().split(":")
    return datetime.time(int(hh), int(mm), tzinfo=datetime.UTC)


def _within(now: datetime.datetime, start: datetime.time, end: datetime.time) -> bool:
    t = now.time()
    return start <= t <= end


class ScheduleWatcher:
    """
    Surveille les transitions de schedules et applique 'flatten_at_end' si requis.

    - On détecte l'ID de schedule actif à chaque tick (en UTC).
    - Si un schedule était actif et ne l'est plus, et qu'il a 'flatten_at_end: true',
      on déclenche un flatten_all() une seule fois à la fin de ce schedule.

    Note: état purement en mémoire (per-process). Si tu veux persister entre runs,
    tu peux ajouter une FileStorage très simple.
    """

    def __init__(self, schedules: List[Dict[str, Any]], logging_enabled: bool = True):
        self.logging_enabled = logging_enabled
        # Prépare les horaires parsés
        self.schedules = []
        for sch in schedules or []:
            sch = dict(sch)
            sch["_start_t"] = _parse_hhmm_utc(sch["start_utc"])
            sch["_end_t"] = _parse_hhmm_utc(sch["end_utc"])
            self.schedules.append(sch)

        self._active_id: Optional[str] = None

    def _current_schedule_id(self, now: Optional[datetime.datetime] = None) -> Optional[str]:
        now = now or datetime.datetime.now(datetime.UTC)
        for sch in self.schedules:
            if _within(now, sch["_start_t"], sch["_end_t"]):
                return sch.get("id")
        return None

    def tick(self, executor) -> None:
        """
        À appeler dans la boucle principale. Déclenche auto-flatten si un schedule
        vient de se terminer et qu'il a 'flatten_at_end: true'.
        """
        now = datetime.datetime.now(datetime.UTC)
        current_id = self._current_schedule_id(now)

        # Entrée dans un nouveau schedule
        if current_id and current_id != self._active_id:
            log(f"[SCHEDULE-WATCH] Entrée dans schedule '{current_id}'", self.logging_enabled)
            self._active_id = current_id
            return

        # Sortie du schedule courant -> check flatten_at_end
        if self._active_id and current_id != self._active_id:
            ended_id = self._active_id
            ended_cfg = next((s for s in self.schedules if s.get("id") == ended_id), None)
            self._active_id = current_id  # peut être None (aucun actif)
            if ended_cfg and (ended_cfg.get("strategy") in (None, {}) or isinstance(ended_cfg.get("strategy"), (str, dict))):
                # 'strategy' peut être un string (nom template) ou un dict résolu (selon quand on passe le watcher).
                # On récupère flatten_at_end du resolved strategy si possible
                flatten_at_end = False
                if isinstance(ended_cfg.get("strategy"), dict):
                    flatten_at_end = bool(ended_cfg["strategy"].get("flatten_at_end", False))
                # Si la stratégie n'est pas résolue ici (string), on essaye de lire un miroir direct au niveau du schedule
                if not flatten_at_end:
                    flatten_at_end = bool(ended_cfg.get("flatten_at_end", False))

                if flatten_at_end:
                    log(f"[SCHEDULE-WATCH] Fin de '{ended_id}' -> Flatten (flatten_at_end=true)", self.logging_enabled)
                    try:
                        executor.flatten_all(instrument="*")
                    except Exception as e:
                        log(f"[SCHEDULE-WATCH] Erreur flatten_at_end: {e}", self.logging_enabled)
                else:
                    log(f"[SCHEDULE-WATCH] Fin de '{ended_id}' (flatten_at_end=false) -> rien à faire", self.logging_enabled)
