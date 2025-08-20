from pathlib import Path
from typing import List
from .services.state_store import StateStore


class CsvWatcher:
    def __init__(self, csv_path: str, state_store: StateStore) -> None:
        self._path = Path(csv_path)
        self._state = state_store

    def read_new_lines(self) -> List[str]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()
            self._state.write_offset(0)
            return []
        offset = self._state.read_offset()
        data = b""
        with open(self._path, "rb") as f:
            f.seek(offset)
            data = f.read()
            new_offset = f.tell()
        if not data:
            return []
        self._state.write_offset(new_offset)
        chunk = data.decode("utf-8", errors="ignore")
        lines = chunk.splitlines()
        return [ln.strip() for ln in lines if ln.strip()]
