"""Hardware auto-discovery.  Every field records whether it was detected."""

from __future__ import annotations

import os
import platform
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import psutil
except ImportError:  # optional dependency
    psutil = None

DEFAULT_L1_BYTES = 32 * 1024


@dataclass
class HardwareProfile:
    system: str
    arch: str
    logical_cores: int
    physical_cores: int
    simd: str
    ram_available_bytes: int
    l1d_bytes: int
    l1d_detected: bool
    notes: list[str] = field(default_factory=list)

    @property
    def tile_elems(self) -> int:
        """Elements per cache tile (half of L1d, 8-byte values, 8-aligned).

        Not used by the scalar language yet; reserved for array operations.
        """
        return max(64, (self.l1d_bytes // 2 // 8) // 8 * 8)

    def to_dict(self) -> dict:
        return asdict(self)

    def describe(self) -> str:
        l1 = f"{self.l1d_bytes // 1024} KB" + ("" if self.l1d_detected else " (assumed)")
        return "\n".join(
            [
                f"OS / arch      : {self.system} / {self.arch}",
                f"Cores          : {self.physical_cores} physical, "
                + f"{self.logical_cores} logical",
                f"SIMD           : {self.simd}",
                f"RAM available  : {self.ram_available_bytes / 2**20:,.0f} MB",
                f"L1 data cache  : {l1}",
            ]
        )


def _x86_simd() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("flags"):
                flags = set(line.split(":", 1)[1].split())
                for flag, name in (
                    ("avx512f", "AVX-512"),
                    ("avx2", "AVX2"),
                    ("avx", "AVX"),
                    ("sse4_2", "SSE4.2"),
                ):
                    if flag in flags:
                        return name
                return "SSE2"
    except OSError:
        pass
    return "unknown (x86-64 baseline: SSE2)"


def _ram_available() -> int:
    if psutil:
        return int(psutil.virtual_memory().available)
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 0


def _l1d() -> tuple[int, bool]:
    base = Path("/sys/devices/system/cpu/cpu0/cache")
    try:
        for idx in sorted(base.glob("index*")):
            if (idx / "level").read_text().strip() == "1" and (
                (idx / "type").read_text().strip() == "Data"
            ):
                size = (idx / "size").read_text().strip().upper()
                mult = {"K": 1024, "M": 1024**2}.get(size[-1], 1)
                return int(size.rstrip("KM")) * mult, True
    except (OSError, ValueError):
        pass
    return DEFAULT_L1_BYTES, False


def scan() -> HardwareProfile:
    arch = platform.machine().lower()
    logical = os.cpu_count() or 1
    physical = (psutil.cpu_count(logical=False) if psutil else None) or logical
    if arch in ("x86_64", "amd64"):
        simd = _x86_simd()
    elif arch in ("aarch64", "arm64"):
        simd = "NEON"
    else:
        simd = "unknown"
    l1, detected = _l1d()
    notes = [] if psutil else ["psutil not installed: physical cores are estimated"]
    return HardwareProfile(
        system=platform.system(),
        arch=arch,
        logical_cores=logical,
        physical_cores=physical,
        simd=simd,
        ram_available_bytes=_ram_available(),
        l1d_bytes=l1,
        l1d_detected=detected,
        notes=notes,
    )
