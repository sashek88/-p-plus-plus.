"""AST node definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Num:
    value: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Call:
    op: str
    args: tuple


@dataclass(frozen=True)
class Block:
    stmts: tuple


@dataclass(frozen=True)
class While:
    cond: object
    body: Block


@dataclass(frozen=True)
class If:
    cond: object
    then: Block
    els: Block | None
