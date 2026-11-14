"""Stage 3: AST -> x86-64 assembly (AT&T syntax, System V ABI, Linux)."""

from __future__ import annotations

from ppp.ast import Block, Call, If, Num, Var, While
from ppp.parser import parse

_BINOPS = {
    "+": ["add %rcx, %rax"],
    "-": ["sub %rcx, %rax"],
    "*": ["imul %rcx, %rax"],
    "^": ["and %rcx, %rax"],
    "|": ["or %rcx, %rax"],
    "<": ["cmp %rcx, %rax", "setl %al", "movzx %al, %rax"],
    ">": ["cmp %rcx, %rax", "setg %al", "movzx %al, %rax"],
    "=": ["cmp %rcx, %rax", "sete %al", "movzx %al, %rax"],
}
_DIV = {
    "/": ["cqo", "idiv %rcx"],
    "%": ["cqo", "idiv %rcx", "mov %rdx, %rax"],
}


class CodeGen:
    def __init__(self) -> None:
        self.out: list[str] = []
        self.names: set[str] = set()
        self._labels = 0

    def _label(self) -> str:
        self._labels += 1
        return f".L{self._labels}"

    def emit(self, *lines: str) -> None:
        self.out.extend(f"  {ln}" for ln in lines)

    def gen(self, n) -> None:
        if isinstance(n, Num):
            self.emit(f"mov ${n.value}, %rax")
        elif isinstance(n, Var):
            self.names.add(n.name)
            self.emit(f"mov v_{n.name}(%rip), %rax")
        elif isinstance(n, Block):
            for s in n.stmts:
                self.gen(s)
        elif isinstance(n, While):
            top, end = self._label(), self._label()
            self.out.append(f"{top}:")
            self.gen(n.cond)
            self.emit("cmp $0, %rax", f"je {end}")
            self.gen(n.body)
            self.emit(f"jmp {top}")
            self.out.append(f"{end}:")
        elif isinstance(n, If):
            self.gen(n.cond)
            self.emit("cmp $0, %rax")
            if n.els is None:
                end = self._label()
                self.emit(f"je {end}")
                self.gen(n.then)
                self.out.append(f"{end}:")
            else:
                els, end = self._label(), self._label()
                self.emit(f"je {els}")
                self.gen(n.then)
                self.emit(f"jmp {end}")
                self.out.append(f"{els}:")
                self.gen(n.els)
                self.out.append(f"{end}:")
        elif isinstance(n, Call):
            self._call(n)
        else:  # pragma: no cover
            raise TypeError(f"unknown node {n!r}")

    def _call(self, n: Call) -> None:
        if n.op == ":":
            name = n.args[0].name
            self.names.add(name)
            self.gen(n.args[1])
            self.emit(f"mov %rax, v_{name}(%rip)")
        elif n.op == "?":
            self.gen(n.args[0])
            self.emit(
                "mov %rax, %rsi",
                "lea fmt(%rip), %rdi",
                "xor %eax, %eax",
                "call printf@PLT",
            )
        else:
            self.gen(n.args[0])
            self.emit("push %rax")
            self.gen(n.args[1])
            self.emit("mov %rax, %rcx", "pop %rax")
            if n.op in _DIV:
                self.emit("test %rcx, %rcx", "jz .Ldivzero")
                self.emit(*_DIV[n.op])
            else:
                self.emit(*_BINOPS[n.op])


def compile_source(src: str) -> str:
    """Compile P++ source text to assembly text."""
    cg = CodeGen()
    cg.gen(parse(src))
    head = [".text", ".globl main", "main:", "  push %rbp", "  mov %rsp, %rbp"]
    tail = [
        "  xor %eax, %eax",
        "  pop %rbp",
        "  ret",
        ".Ldivzero:",  # runtime safeguard: division by zero
        "  and $-16, %rsp",
        "  lea msg_div(%rip), %rdi",
        "  call puts@PLT",
        "  mov $1, %eax",
        "  leave",
        "  ret",
        ".section .rodata",
        'fmt: .asciz "%ld\\n"',
        'msg_div: .asciz "P++ runtime error: division by zero"',
        ".bss",
    ]
    tail += [f".comm v_{name}, 8, 8" for name in sorted(cg.names)]
    tail.append('.section .note.GNU-stack,"",@progbits')
    return "\n".join(head + cg.out + tail) + "\n"
