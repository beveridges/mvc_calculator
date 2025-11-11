# tests/test_build_py_core.py
import pytest, tempfile, textwrap
from pathlib import Path
import importlib.util

@pytest.fixture(params=["BERNSTEIN_BUILD", "MVC_BUILD"])
def builder_module(request):
    path = os.environ.get(request.param)
    if not path:
        pytest.skip(f"{request.param} env var not set")
    spec = importlib.util.spec_from_file_location(request.param.lower(), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_read_previous_from_file(builder_module, tmp_path):
    """Ensure both build.py variants can read version_info correctly."""
    util_dir = tmp_path / "utilities"
    util_dir.mkdir()
    (util_dir / "version_info.py").write_text(textwrap.dedent("""
        BUILDNUMBER = "25.11-alpha.01.01"
        VERSIONNUMBER = "25.11-alpha.01"
    """), encoding="utf-8")

    prev_build, prev_version = builder_module.read_previous_from_file(tmp_path)
    assert prev_build == "25.11-alpha.01.01"
    assert prev_version == "25.11-alpha.01"
