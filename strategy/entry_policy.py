# strategy/entry_policy.py
from __future__ import annotations

from typing import Any, Dict, Tuple, Optional
from utils.schedule_gate import ScheduleGate


class EntryPolicy:
    """
    Décide si on peut entrer en position en fonction des schedules (fenêtres + quotas).
    Retourne (ok, reason, schedule_resolu) pour paramétrer l'exécution (lots, stratégie A/B, TP ticks, etc.).
    """
    def __init__(self, schedule_gate: ScheduleGate):
        self.schedule_gate = schedule_gate

    def should_enter(self, signal: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        ok, sid, used, max_allowed = self.schedule_gate.can_enter()
        if not sid:
            return False, "outside_schedules", None
        if not ok:
            return False, f"quota_exhausted:{sid} ({used}/{max_allowed})", None
        schedule = self.schedule_gate.get_schedule(sid)
        return True, f"allowed:{sid}", schedule

    def commit_entry(self, schedule_id: str) -> None:
        self.schedule_gate.mark_entry(schedule_id)
