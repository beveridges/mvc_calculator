"""Ensure Windows PyInstaller build collects h5py (MATLAB v7.3 / HDF5 .mat)."""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD_SCRIPT = REPO / "___BUILD___" / "build_windows_portable.py"


def test_portable_build_script_collects_h5py():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "--collect-all" in text
    assert '"h5py"' in text or "'h5py'" in text
    assert "import h5py" in text
    assert "hdf5*.dll" in text or "libhdf5*.dll" in text


def test_h5py_hook_exists():
    hook = REPO / "hooks" / "hook-h5py.py"
    assert hook.exists()
    h = hook.read_text(encoding="utf-8")
    assert "collect_all" in h or "collect_all(" in h
    assert "h5py" in h
