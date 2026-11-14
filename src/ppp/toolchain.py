"""Assemble, link and run.  Uses the system C compiler driver as assembler/linker."""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from ppp.errors import PPlusError
from ppp.safeguards import DEFAULT_TIMEOUT_S


@dataclass
class RunResult:
    stdout: str
    returncode: int
    seconds: float


def find_driver() -> str:
    for name in ("gcc", "cc", "clang"):
        path = shutil.which(name)
        if path:
            return path
    raise PPlusError(
        "no gcc/cc/clang found (needed to assemble and link). "
        "Install one, e.g. 'sudo apt install gcc'."
    )


def check_platform() -> None:
    if platform.system() != "Linux" or platform.machine().lower() not in (
        "x86_64",
        "amd64",
    ):
        raise PPlusError(
            "P++ currently targets x86-64 Linux "
            f"(this machine: {platform.system()} {platform.machine()})"
        )


def build(asm: str, out: Path, keep_asm: Path | None = None) -> Path:
    """Assemble and link `asm` into an executable at `out`."""
    check_platform()
    driver = find_driver()
    with tempfile.TemporaryDirectory() as tmp:
        asm_path = keep_asm or Path(tmp) / "prog.s"
        asm_path.write_text(asm)
        proc = subprocess.run(
            [driver, str(asm_path), "-o", str(out)],
            capture_output=True,
            text=True,
            check=False,
        )
    if proc.returncode != 0:
        raise PPlusError(f"assembler/linker failed:\n{proc.stderr.strip()}")
    return out


def run(exe: Path, timeout: float = DEFAULT_TIMEOUT_S) -> RunResult:
    """Run a built program under a watchdog timeout."""
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [str(exe)], capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise PPlusError(
            f"watchdog: program ran longer than {timeout:g}s and was killed "
            "(infinite loop?)"
        ) from exc
    return RunResult(proc.stdout, proc.returncode, time.perf_counter() - start)
