from conftest import needs_toolchain, run_ppp

pytestmark = needs_toolchain


def out(src: str) -> list[int]:
    res = run_ppp(src)
    assert res.returncode == 0
    return [int(x) for x in res.stdout.split()]


def test_arithmetic_precedence_is_structural():
    assert out("? + 2 * 3 4") == [14]
    assert out("? - 10 4") == [6]
    assert out("? % 17 5") == [2]
    assert out("? / 17 5") == [3]


def test_comparisons_and_logic():
    assert out("? < 1 2 ? > 1 2 ? = 3 3 ? ^ 1 0 ? | 1 0") == [1, 0, 1, 0, 1]


def test_variables_and_loop():
    assert out(": @i 1 : @s 0 & < @i 101 ( : @s + @s @i : @i + @i 1 ) ? @s") == [5050]


def test_if_and_else():
    assert out("!? 1 ( ? 7 ) !? 0 ( ? 8 )") == [7]
    assert out("!?-! 0 ( ? 1 ) ( ? 2 )") == [2]


def test_nested_loop_if():
    src = """
    : @i 1
    & < @i 7 (
      !?-! = % @i 2 0 ( ? 0 ) ( ? @i )
      : @i + @i 1
    )
    """
    assert out(src) == [1, 0, 3, 0, 5, 0]


def test_division_by_zero_is_a_clean_error():
    res = run_ppp("? / 1 0")
    assert res.returncode == 1
    assert "division by zero" in res.stdout


def test_negative_numbers_via_subtraction():
    assert out("? - 0 5") == [-5]
