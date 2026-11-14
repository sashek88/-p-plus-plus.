import pytest
from conftest import needs_toolchain

from ppp import hardware, safeguards, toolchain
from ppp.errors import PPlusError, SafeguardError


def test_hardware_scan_has_sane_values():
    hw = hardware.scan()
    assert hw.logical_cores >= 1 and hw.l1d_bytes > 0 and hw.tile_elems % 8 == 0


def test_source_size_limit():
    with pytest.raises(SafeguardError):
        safeguards.check_source_size("1" * (safeguards.MAX_SOURCE_BYTES + 1))


def test_thermal_check_does_not_crash():
    safeguards.check_thermal(limit_c=500)


@needs_toolchain
def test_watchdog_kills_infinite_loop(tmp_path):
    from ppp import compile_source

    exe = toolchain.build(compile_source("& 1 ( : @x 1 )"), tmp_path / "loop")
    with pytest.raises(PPlusError, match="watchdog"):
        toolchain.run(exe, timeout=0.5)
