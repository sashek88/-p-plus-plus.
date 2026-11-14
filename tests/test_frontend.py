import pytest

from ppp import PPlusError, compile_source
from ppp.ast import Call, If, Num, While
from ppp.lexer import lex
from ppp.parser import parse


def test_lexer_longest_match_and_comments():
    toks = [t.text for t in lex("!?-! !? ! # ignored\n@x 12")]
    assert toks == ["!?-!", "!?", "!", "@x", "12"]


def test_lexer_tracks_lines():
    assert lex("1\n\n  2")[1].line == 3


def test_parse_prefix_expression():
    prog = parse("+ 1 * 2 3")
    assert prog.stmts[0] == Call("+", (Num(1), Call("*", (Num(2), Num(3)))))


def test_parse_loop_and_if():
    prog = parse("& 1 ( ? 1 ) !?-! 1 ( ? 2 ) ( ? 3 )")
    assert isinstance(prog.stmts[0], While)
    assert isinstance(prog.stmts[1], If) and prog.stmts[1].els is not None


@pytest.mark.parametrize(
    "src",
    [
        "$ 1",  # unknown symbol
        "+ 1",  # missing operand
        ": 5 3",  # assign to non-variable
        "& 1 2",  # loop needs a block
        "( ? 1",  # missing )
        ")",  # unmatched )
        "abc",  # bad character
        "+ 1 ( ? 1 )",  # block as a value
    ],
)
def test_syntax_errors(src):
    with pytest.raises(PPlusError):
        compile_source(src)


def test_error_has_position():
    with pytest.raises(PPlusError) as e:
        compile_source("? 1\n$ 2")
    assert e.value.line == 2
