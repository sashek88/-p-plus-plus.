"""Command-line interface: run | build | bench | audit | info."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
from pathlib import Path

from ppp import __version__, hardware, safeguards, toolchain
from ppp.codegen import compile_source
from ppp.errors import PPlusError


def _source(args: argparse.Namespace) -> str:
    if args.code is not None:
        src = args.code
    elif args.file:
        src = Path(args.file).read_text(encoding="utf-8")
    else:
        raise PPlusError("give a source file or -c 'code'")
    safeguards.check_source_size(src)
    return src


def _preflight(args: argparse.Namespace) -> None:
    if not getattr(args, "no_thermal_check", False):
        safeguards.check_thermal()


def cmd_run(args: argparse.Namespace) -> int:
    _preflight(args)
    asm = compile_source(_source(args))
    with tempfile.TemporaryDirectory() as tmp:
        exe = toolchain.build(asm, Path(tmp) / "prog")
        res = toolchain.run(exe, timeout=args.timeout)
    sys.stdout.write(res.stdout)
    return res.returncode


def cmd_build(args: argparse.Namespace) -> int:
    asm = compile_source(_source(args))
    if args.emit_asm:
        Path(args.emit_asm).write_text(asm)
        print(f"wrote assembly to {args.emit_asm}")
        return 0
    out = Path(args.output)
    toolchain.build(asm, out)
    print(f"built {out}")
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    _preflight(args)
    asm = compile_source(_source(args))
    times: list[float] = []
    with tempfile.TemporaryDirectory() as tmp:
        exe = toolchain.build(asm, Path(tmp) / "prog")
        for _ in range(args.runs):
            times.append(toolchain.run(exe, timeout=args.timeout).seconds * 1000)
    report = {
        "runs": args.runs,
        "min_ms": min(times),
        "median_ms": statistics.median(times),
        "max_ms": max(times),
        "hardware": hardware.scan().to_dict(),
    }
    Path(args.output).write_text(json.dumps(report, indent=2))
    print(
        f"{args.runs} runs: min {report['min_ms']:.2f} ms, "
        f"median {report['median_ms']:.2f} ms, max {report['max_ms']:.2f} ms"
    )
    print(f"saved to {args.output}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    cur = json.loads(Path(args.current).read_text())
    base = json.loads(Path(args.baseline).read_text())
    limit = base["median_ms"] * args.tolerance
    ok = cur["median_ms"] <= limit
    print(
        f"median {cur['median_ms']:.2f} ms vs baseline {base['median_ms']:.2f} ms "
        f"(allowed up to {limit:.2f} ms): {'PASS' if ok else 'REGRESSION'}"
    )
    return 0 if ok else 1


def cmd_info(_args: argparse.Namespace) -> int:
    print(f"P++ {__version__}\n")
    print(hardware.scan().describe())
    temp = safeguards.cpu_temperature_c()
    print(f"CPU temperature: {'unavailable' if temp is None else f'{temp:.0f} C'}")
    try:
        print(f"C driver       : {toolchain.find_driver()}")
        toolchain.check_platform()
        print("Target         : OK (x86-64 Linux)")
    except PPlusError as exc:
        print(f"Toolchain      : PROBLEM - {exc.message}")
    return 0


def _add_source(p: argparse.ArgumentParser) -> None:
    p.add_argument("file", nargs="?", help="P++ source file (.ppp)")
    p.add_argument("-c", "--code", help="inline P++ source instead of a file")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ppp", description="P++ compiler")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="compile and run a program")
    _add_source(p)
    p.add_argument("--timeout", type=float, default=safeguards.DEFAULT_TIMEOUT_S)
    p.add_argument("--no-thermal-check", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("build", help="compile to an executable or assembly")
    _add_source(p)
    p.add_argument("-o", "--output", default="a.out")
    p.add_argument("--emit-asm", metavar="FILE", help="write assembly and stop")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("bench", help="time a program over several runs")
    _add_source(p)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("-o", "--output", default="bench.json")
    p.add_argument("--timeout", type=float, default=safeguards.DEFAULT_TIMEOUT_S)
    p.add_argument("--no-thermal-check", action="store_true")
    p.set_defaults(func=cmd_bench)

    p = sub.add_parser("audit", help="compare a bench result against a baseline")
    p.add_argument("current")
    p.add_argument("--baseline", required=True)
    p.add_argument("--tolerance", type=float, default=1.5, help="allowed slowdown x")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("info", help="show detected hardware and toolchain")
    p.set_defaults(func=cmd_info)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PPlusError as exc:
        print(f"ppp: error: {exc}", file=sys.stderr)
        return 2
