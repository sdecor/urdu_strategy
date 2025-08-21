from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union


# ----------------------------- Core "latest-line" reader -----------------------------

@dataclass
class CsvLatestConfig:
    path: Path
    schema: List[str]
    delimiter: str = ","
    has_header: bool = True


class CsvLatestReader:
    def __init__(self, cfg: CsvLatestConfig) -> None:
        self.cfg = cfg
        self._last_fingerprint: Optional[str] = None

    def _read_last_nonempty_line(self) -> Optional[str]:
        p = self.cfg.path
        if not p.exists() or p.stat().st_size == 0:
            return None
        with p.open("r", encoding="utf-8", newline="") as f:
            lines = f.readlines()
        if not lines:
            return None
        if self.cfg.has_header and len(lines) <= 1:
            return None
        # drop trailing empty lines
        i = len(lines) - 1
        while i >= 0 and not lines[i].strip():
            i -= 1
        if i < 0:
            return None
        if self.cfg.has_header and i == 0:
            return None
        return lines[i]

    def _fingerprint(self, line: str) -> str:
        p = self.cfg.path
        stat = p.stat()
        return f"{stat.st_mtime_ns}:{stat.st_size}:{hash(line)}"

    def read_latest_record(self) -> Optional[Dict[str, str]]:
        """
        Retourne uniquement la DERNIÈRE ligne non vide du CSV,
        une seule fois (dédupliquée via fingerprint). None si rien de nouveau.
        """
        line = self._read_last_nonempty_line()
        if line is None:
            return None
        fp = self._fingerprint(line)
        if fp == self._last_fingerprint:
            return None  # déjà traité
        self._last_fingerprint = fp

        reader = csv.reader([line], delimiter=self.cfg.delimiter)
        row = next(reader, None)
        if row is None:
            return None

        # normaliser taille
        cols = list(row)
        if len(cols) < len(self.cfg.schema):
            cols += [""] * (len(self.cfg.schema) - len(cols))
        elif len(cols) > len(self.cfg.schema):
            cols = cols[: len(self.cfg.schema)]

        return dict(zip(self.cfg.schema, cols))


def build_latest_reader(
    csv_path: Union[str, Path],
    schema: List[str],
    delimiter: str = ",",
    has_header: bool = True,
) -> CsvLatestReader:
    cfg = CsvLatestConfig(path=Path(csv_path), schema=schema, delimiter=delimiter, has_header=has_header)
    return CsvLatestReader(cfg)


# ----------------------------- Back-compat wrapper -----------------------------

class CsvWatcher:
    """
    Compatibilité avec l'ancien constructeur:
      CsvWatcher(csv_path=..., state_store=..., schema=..., delimiter=',', has_header=True)

    Ignore `state_store` (plus d'offset: on ne lit que la dernière ligne).
    Expose la même méthode attendue: `read_latest_record()`.
    """

    def __init__(
        self,
        csv_path: Union[str, Path],
        state_store: object = None,  # conservé pour compat
        schema: Optional[List[str]] = None,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> None:
        self._reader = build_latest_reader(
            csv_path=csv_path,
            schema=schema or ["received_at", "content_type", "raw"],
            delimiter=delimiter,
            has_header=has_header,
        )

    def read_latest_record(self) -> Optional[Dict[str, str]]:
        return self._reader.read_latest_record()
