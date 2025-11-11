# tests/test_build_py_increment.py
import os
import importlib.util
import pytest

@pytest.fixture(params=["BERNSTEIN_BUILD", "MVC_BUILD"])
def builder_module(request):
    """Dynamically import build.py under test using environment vars."""
    path = os.environ.get(request.param)
    if not path:
        pytest.skip(f"{request.param} not set")
    spec = importlib.util.spec_from_file_location(request.param.lower(), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("input_val, expected", [
    ("25.11-alpha.01.00", "01"),   # normal increment
    ("25.11.09", "10"),            # numeric rollover
    ("", "00"),                    # empty string
    ("25.alpha.x", "00"),          # non-digit ending
    ("123", "124"),                # plain number
    ("v1.09", "10"),               # with prefix and leading zero
])
def test_increment_last_segment(builder_module, input_val, expected):
    """Ensure increment_last_segment handles numeric endings consistently."""
    func = builder_module.increment_last_segment

    result = func(input_val)

    # handle tuple vs str difference
    if isinstance(result, tuple):
        formatted, numeric = result
        assert formatted == expected
        assert isinstance(numeric, int)
    else:
        assert result == expected
