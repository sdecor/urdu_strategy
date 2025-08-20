from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_local_key(tz_name: str = "Europe/Zurich") -> str:
    tz = ZoneInfo(tz_name)
    return datetime.now(tz).strftime("%Y-%m-%d")


def _parse_hhmm(s: str) -> time:
    s = (s or "00:00").strip()
    hh, mm = s.split(":")
    return time(hour=int(hh), minute=int(mm))


def trading_day_key(tz_name: str = "Europe/Zurich", reset_time_local: str = "00:00") -> str:
    """
    Retourne une clé 'YYYY-MM-DD' représentant le jour de trading courant,
    commençant à reset_time_local (ex: 05:00). Si l'heure actuelle est avant
    l'heure de reset, on renvoie la date de la veille.
    """
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    rt = _parse_hhmm(reset_time_local)
    reset_today = datetime.combine(now.date(), rt, tzinfo=tz)
    if now < reset_today:
        return (now - timedelta(days=1)).date().isoformat()
    return now.date().isoformat()
