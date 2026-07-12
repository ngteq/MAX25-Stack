"""Simple AX.25 source ban list for max25d — silent RX drop."""
from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Optional

DEFAULT_BANS_FILE = Path("/etc/max25/bans.txt")

_AX25_UI_SRC_RE = re.compile(r"\[AX25 UI ([^>]+)>")


def extract_ax25_source(line: str) -> Optional[str]:
    """Return source callsign from a formatted AX.25 UI RX line, or None."""
    match = _AX25_UI_SRC_RE.search(line)
    if not match:
        return None
    return match.group(1).strip().upper()


def callsign_banned(ban_entry: str, source: str) -> bool:
    """Match ban entry against an incoming source callsign."""
    ban = ban_entry.strip().upper()
    src = source.strip().upper()
    if not ban or not src:
        return False
    if "-" in ban:
        return ban == src
    return ban == src.split("-", 1)[0]


class BanList:
    """Persistent set of banned AX.25 source addresses."""

    def __init__(self, path: Path | str = DEFAULT_BANS_FILE) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._entries: set[str] = set()
        self.load()

    def load(self) -> None:
        entries: set[str] = set()
        if self.path.is_file():
            text = self.path.read_text(encoding="utf-8")
            for raw in text.splitlines():
                line = raw.split("#", 1)[0].strip().upper()
                if line:
                    entries.add(line)
        with self._lock:
            self._entries = entries

    def save(self) -> None:
        lines = sorted(self._entries)
        content = "\n".join(lines)
        if content:
            content += "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding="utf-8")

    def list(self) -> list[str]:
        with self._lock:
            return sorted(self._entries)

    def add(self, callsign: str) -> None:
        call = callsign.strip().upper()
        with self._lock:
            self._entries.add(call)
            self.save()

    def remove(self, callsign: str) -> bool:
        call = callsign.strip().upper()
        with self._lock:
            if call not in self._entries:
                return False
            self._entries.remove(call)
            self.save()
            return True

    def is_banned(self, source: str) -> bool:
        src = source.strip().upper()
        if not src:
            return False
        with self._lock:
            return any(callsign_banned(entry, src) for entry in self._entries)
