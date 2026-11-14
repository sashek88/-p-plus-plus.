"""P++ compiler: symbol-based prefix language -> x86-64 assembly."""

from ppp.codegen import compile_source
from ppp.errors import PPlusError

__all__ = ["PPlusError", "compile_source"]
__version__ = "0.1.0"
