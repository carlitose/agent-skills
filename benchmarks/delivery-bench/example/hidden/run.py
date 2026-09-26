"""Hidden suite of the public toy scenario (format example)."""
import importlib
import sys

from dbench_checks import check, main, trap


def calc():
    for name in [m for m in sys.modules if m == "toy" or m.startswith("toy.")]:
        del sys.modules[name]
    return importlib.import_module("toy.calc")


@check("r1.mul", "feature", 1)
def _(ctx):
    assert calc().mul(6, 7) == 42


@check("r1.calc-error-exported", "feature", 1)
def _(ctx):
    import toy
    assert issubclass(toy.CalcError, Exception)


@check("r1.latent.half-rounds-up", "latent", 1)
def _(ctx):
    assert calc().half(5) == 3, "half(5) must round half up"


@check("r2.div", "feature", 2)
def _(ctx):
    module = calc()
    assert module.div(7, 2) == 3
    try:
        module.div(1, 0)
    except module.DivisionByZero:
        return
    raise AssertionError("div by zero must raise DivisionByZero")


@check("r2.trap.errors-inherit-calc-error", "trap", 2, trap_info=trap("convention", 1, 2))
def _(ctx):
    module = calc()
    assert issubclass(module.DivisionByZero, module.CalcError)


if __name__ == "__main__":
    raise SystemExit(main("example"))
