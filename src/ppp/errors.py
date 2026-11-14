"""Error types shared by every stage."""

from __future__ import annotations


class PPlusError(Exception):
    """A user-facing P++ error, with an optional source position."""

    def __init__(self, message: str, line: int = 0, col: int = 0) -> None:
        self.message = message
        self.line = line
        self.col = col
        where = f"line {line}, col {col}: " if line else ""
        super().__init__(f"{where}{message}")


class SafeguardError(PPlusError):
    """A hardware or resource safeguard refused to continue."""
