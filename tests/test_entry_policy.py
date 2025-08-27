# tests/test_entry_policy.py
from utils.schedule_gate import ScheduleGate, FileSessionStorage
from strategy.entry_policy import EntryPolicy


def test_quota_morning_and_day(tmp_path, monkeypatch):
    # Schedules (pas besoin de strategy pour tester quotas)
    schedules = [
        {"id": "morning", "start_utc": "06:00", "end_utc": "09:55", "max_trades": 1},
        {"id": "day",     "start_utc": "10:00", "end_utc": "16:00", "max_trades": 1},
    ]

    storage = FileSessionStorage(str(tmp_path / "session_gate.json"))
    gate = ScheduleGate(
        schedules_config=schedules,
        storage=storage,
        logging_enabled=False,
        strategy_templates=[],
    )
    policy = EntryPolicy(gate)

    # Force la fenêtre active à "morning"
    monkeypatch.setattr(gate, "current_schedule_id", lambda now=None: "morning")

    # 1er trade dans morning -> OK
    ok, reason, schedule = policy.should_enter({"instrument": "X", "side": "long"})
    assert ok is True
    assert schedule and schedule["id"] == "morning"
    policy.commit_entry(schedule_id=schedule["id"])

    # 2e trade dans morning -> refus (quota épuisé)
    ok, reason, schedule = policy.should_enter({"instrument": "X", "side": "short"})
    assert ok is False
    assert "quota_exhausted:morning" in reason

    # Bascule sur "day"
    monkeypatch.setattr(gate, "current_schedule_id", lambda now=None: "day")

    # 1er trade dans day -> OK
    ok, reason, schedule = policy.should_enter({"instrument": "X", "side": "long"})
    assert ok is True
    assert schedule and schedule["id"] == "day"
    policy.commit_entry(schedule_id=schedule["id"])

    # 2e trade dans day -> refus (quota épuisé)
    ok, reason, schedule = policy.should_enter({"instrument": "X", "side": "short"})
    assert ok is False
    assert "quota_exhausted:day" in reason
