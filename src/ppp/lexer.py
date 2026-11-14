"""Stage 1: source text -> tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ppp.errors import PPlusError

_TOKEN = re.compile(
    r"""
    (?P<WS>[ \t\r]+)
  | (?P<NL>\n)
  | (?P<COMMENT>\#[^\n]*)
  | (?P<NUM>\d+)
  | (?P<VAR>@[A-Za-z_][A-Za-z0-9_]*)
  | (?P<OP>!\?-!|!\?|[^\s\w])
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Token:
    kind: str  # NUM | VAR | OP
    text: str
    line: int
    col: int


def lex(src: str) -> list[Token]:
    tokens: list[Token] = []
    pos, line, line_start = 0, 1, 0
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if m is None:
            raise PPlusError(
                f"unexpected character {src[pos]!r}", line, pos - line_start + 1
            )
        kind = m.lastgroup
        if kind == "NL":
            line += 1
            line_start = m.end()
        elif kind in ("NUM", "VAR", "OP"):
            tokens.append(Token(kind, m.group(), line, m.start() - line_start + 1))
        pos = m.end()
    return tokens
