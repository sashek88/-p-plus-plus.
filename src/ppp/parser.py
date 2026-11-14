"""Stage 2: tokens -> AST.  Prefix notation: every symbol has a fixed arity."""

from __future__ import annotations

from ppp.ast import Block, Call, If, Num, Var, While
from ppp.errors import PPlusError
from ppp.lexer import Token, lex

BINARY = set("+-*/%<>=^|")  # ^ = and, | = or
STATEMENT_NODES = (Block, While, If)


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.toks = tokens
        self.pos = 0

    def _next(self) -> Token:
        if self.pos >= len(self.toks):
            last = self.toks[-1] if self.toks else None
            raise PPlusError(
                "unexpected end of program",
                last.line if last else 0,
                last.col if last else 0,
            )
        tok = self.toks[self.pos]
        self.pos += 1
        return tok

    def _value(self, what: str):
        start = self.toks[self.pos] if self.pos < len(self.toks) else None
        node = self.node()
        if isinstance(node, STATEMENT_NODES):
            t = start or self.toks[-1]
            raise PPlusError(
                f"{what} needs a value, not a block/loop/if", t.line, t.col
            )
        return node

    def _block(self, what: str) -> Block:
        tok = self._next()
        if tok.text != "(":
            raise PPlusError(f"{what} needs a ( ... ) block", tok.line, tok.col)
        stmts = []
        while True:
            if self.pos >= len(self.toks):
                raise PPlusError("missing ')'", tok.line, tok.col)
            if self.toks[self.pos].text == ")":
                self.pos += 1
                return Block(tuple(stmts))
            stmts.append(self.node())

    def node(self):
        tok = self._next()
        if tok.kind == "NUM":
            return Num(int(tok.text))
        if tok.kind == "VAR":
            return Var(tok.text[1:])
        op = tok.text
        if op == "(":
            self.pos -= 1
            return self._block("block")
        if op == ")":
            raise PPlusError("unmatched ')'", tok.line, tok.col)
        if op in BINARY:
            return Call(op, (self._value(f"'{op}'"), self._value(f"'{op}'")))
        if op == "?":
            return Call("?", (self._value("'?'"),))
        if op == ":":
            target = self._next()
            if target.kind != "VAR":
                raise PPlusError(
                    "':' needs a variable first, like : @x 5", target.line, target.col
                )
            return Call(":", (Var(target.text[1:]), self._value("':'")))
        if op == "&":
            return While(self._value("'&'"), self._block("'&'"))
        if op in ("!?", "!?-!"):
            cond = self._value(f"'{op}'")
            then = self._block(f"'{op}'")
            els = self._block("'!?-!' else") if op == "!?-!" else None
            return If(cond, then, els)
        raise PPlusError(f"unknown symbol {op!r}", tok.line, tok.col)


def parse(src: str) -> Block:
    p = _Parser(lex(src))
    stmts = []
    while p.pos < len(p.toks):
        stmts.append(p.node())
    return Block(tuple(stmts))
