# P++

A small symbol-based language with **prefix notation** that compiles straight to
**x86-64 assembly** (Linux). Every symbol is a function with a fixed number of
arguments, so there are no keywords, no parentheses for math and no precedence rules.

```
: @i 1
: @s 0
& < @i 101 (          # while i < 101
  : @s + @s @i        # s = s + i
  : @i + @i 1
)
? @s                  # prints 5050
```

## Symbols

| Symbol | Meaning | Args |
|---|---|---|
| `+ - * / %` | arithmetic | 2 |
| `< > =` | less, greater, equal (give 1 or 0) | 2 |
| `^` `\|` | and, or | 2 |
| `:` | assign: `: @x 5` | variable, value |
| `?` | print | 1 |
| `&` | while loop: `& cond ( body )` | condition, block |
| `!?` | if: `!? cond ( then )` | condition, block |
| `!?-!` | if/else: `!?-! cond ( then ) ( else )` | condition, 2 blocks |
| `@name` | variable | 0 |
| `( ... )` | block | any |
| `#` | comment to end of line | |

All values are 64-bit signed integers. Division by zero stops the program with a clear error.

## Install and use

Requires Python 3.10+, Linux x86-64, and `gcc` (or `cc`/`clang`) to assemble and link.

```bash
pip install -e ".[hw,dev]"
ppp info                       # detected hardware and toolchain
ppp run examples/loop.ppp      # compile + run (10 s watchdog by default)
ppp run -c '? + 2 3'           # inline code
ppp build examples/loop.ppp -o loop
ppp build examples/loop.ppp --emit-asm loop.s
ppp bench examples/loop.ppp --runs 10 -o baseline.json
ppp bench examples/loop.ppp --runs 10 -o current.json
ppp audit current.json --baseline baseline.json --tolerance 1.5
```

## Layout

```
src/ppp/
  lexer.py       text -> tokens (with line/column for errors)
  parser.py      tokens -> AST (fixed-arity prefix parsing)
  ast.py         node types
  codegen.py     AST -> x86-64 assembly
  toolchain.py   assemble / link / run with a watchdog timeout
  hardware.py    CPU, SIMD, RAM and L1 cache discovery
  safeguards.py  source-size limit, thermal check
  cli.py         run | build | bench | audit | info
tests/           frontend, end-to-end and safety tests
examples/        sample programs
```

## Safeguards

Watchdog timeout (kills infinite loops), source-size limit, pre-run CPU temperature
check (where the OS exposes it), and a runtime division-by-zero check. These are
guard rails for your session; CPUs already protect themselves in hardware.

## Roadmap

1. Functions bound to symbols (`@`)
2. Strings (`"`)
3. Array/vector operations, which will use the hardware profile (SIMD width, cache
   tile size) for vectorized code. The profile is already collected by `ppp info`.
4. ARM64 backend
