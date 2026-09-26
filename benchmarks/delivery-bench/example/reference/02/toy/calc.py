"""Integer helpers."""


class CalcError(Exception):
    """Base of every error in the package."""


class DivisionByZero(CalcError):
    """Raised by div when the divisor is zero."""


def add(a: int, b: int) -> int:
    return a + b


def mul(a: int, b: int) -> int:
    return a * b


def div(a: int, b: int) -> int:
    if b == 0:
        raise DivisionByZero("division by zero")
    return a // b


def half(value: int) -> int:
    """Half of value, rounded half up."""
    return (value + 1) // 2
