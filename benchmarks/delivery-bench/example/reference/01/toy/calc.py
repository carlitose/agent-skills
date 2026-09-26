"""Integer helpers."""


class CalcError(Exception):
    """Base of every error in the package."""


def add(a: int, b: int) -> int:
    return a + b


def mul(a: int, b: int) -> int:
    return a * b


def half(value: int) -> int:
    """Half of value, rounded half up."""
    return (value + 1) // 2
