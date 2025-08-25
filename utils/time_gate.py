from datetime import datetime, time


class TimeBasedGate:
    def __init__(self, start_str: str, stop_str: str):
        """
        Args:
            start_str (str): Heure de début en format HH:MM (ex. '02:00')
            stop_str (str): Heure de fin en format HH:MM (ex. '20:05')
        """
        self.start_time = self._parse_time(start_str)
        self.stop_time = self._parse_time(stop_str)

    def _parse_time(self, time_str: str) -> time:
        hours, minutes = map(int, time_str.split(":"))
        return time(hour=hours, minute=minutes)

    def is_within_trading_hours(self) -> bool:
        now = datetime.utcnow().time()
        return self.start_time <= now < self.stop_time

    def is_shutdown_time(self) -> bool:
        now = datetime.utcnow().time()
        return now >= self.stop_time
