"""Resource safeguards.

These protect your session (hangs, runaway memory, a hot machine).
They are advisory guard rails: CPUs already throttle themselves in hardware.
"""

from __future__ import annotations

from pathlib import Path

from ppp.errors import SafeguardError

DEFAULT_TIMEOUT_S = 10.0
MAX_SOURCE_BYTES = 1_000_000
DEFAULT_TEMP_LIMIT_C = 90.0


def check_source_size(src: str) -> None:
    if len(src.encode()) > MAX_SOURCE_BYTES:
        raise SafeguardError(f"source larger than {MAX_SOURCE_BYTES:,} bytes")


def cpu_temperature_c() -> float | None:
    """Hottest CPU-like thermal zone in Celsius, or None if unavailable."""
    temps = []
    for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
        try:
            kind = (zone / "type").read_text().strip().lower()
            if any(k in kind for k in ("cpu", "x86_pkg", "soc", "core")):
                temps.append(int((zone / "temp").read_text()) / 1000.0)
        except (OSError, ValueError):
            continue
    return max(temps) if temps else None


def check_thermal(limit_c: float = DEFAULT_TEMP_LIMIT_C) -> float | None:
    temp = cpu_temperature_c()
    if temp is not None and temp > limit_c:
        raise SafeguardError(
            f"CPU is at {temp:.0f}C (limit {limit_c:.0f}C); let it cool down first"
        )
    return temp
