import tempfile
from pathlib import Path

import pytest

from ppp import PPlusError, compile_source, toolchain


def _can_run() -> bool:
    try:
        toolchain.check_platform()
        toolchain.find_driver()
    except PPlusError:
        return False
    return True


needs_toolchain = pytest.mark.skipif(
    not _can_run(), reason="needs x86-64 Linux with gcc/cc/clang"
)


def run_ppp(src: str) -> toolchain.RunResult:
    with tempfile.TemporaryDirectory() as tmp:
        exe = toolchain.build(compile_source(src), Path(tmp) / "prog")
        return toolchain.run(exe, timeout=5)
