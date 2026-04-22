"""
Shared pytest configuration for the MVC Calculator test suite.

- Ensures the project root is importable.
- Disables network-dependent behaviour and real license enforcement.
- Provides a QApplication fixture that is safely reused across UI tests.
- Auto-skips UI tests when PyQt5 is unavailable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path: make the repo root importable for `import main`, `import plot_controller`, etc.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Environment hygiene: make sure nothing in the test suite accidentally
# enforces the license or emits telemetry over the network.
# ---------------------------------------------------------------------------
os.environ.setdefault("LICENSE_CHECK", "0")
os.environ.setdefault("TELEMETRY", "0")
os.environ.setdefault("PREACTIVATED_LAUNCH_REPORT", "0")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

# ---------------------------------------------------------------------------
# PyQt5 detection helpers
# ---------------------------------------------------------------------------
try:
    from PyQt5.QtWidgets import QApplication  # noqa: F401
    HAS_PYQT5 = True
except Exception:  # pragma: no cover - environment without Qt
    HAS_PYQT5 = False

try:
    import numpy  # noqa: F401
    HAS_NUMPY = True
except Exception:  # pragma: no cover
    HAS_NUMPY = False

try:
    import scipy  # noqa: F401
    HAS_SCIPY = True
except Exception:  # pragma: no cover
    HAS_SCIPY = False


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip tests that require optional dependencies when they
    aren't available in the test environment.
    """
    skip_qt = pytest.mark.skip(reason="PyQt5 not installed")
    skip_numpy = pytest.mark.skip(reason="numpy not installed")
    skip_scipy = pytest.mark.skip(reason="scipy not installed")

    for item in items:
        if "requires_qt" in item.keywords and not HAS_PYQT5:
            item.add_marker(skip_qt)
        if "requires_numpy" in item.keywords and not HAS_NUMPY:
            item.add_marker(skip_numpy)
        if "requires_scipy" in item.keywords and not HAS_SCIPY:
            item.add_marker(skip_scipy)


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_qt: test needs PyQt5")
    config.addinivalue_line("markers", "requires_numpy: test needs numpy")
    config.addinivalue_line("markers", "requires_scipy: test needs scipy")


# ---------------------------------------------------------------------------
# Shared QApplication fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication for the entire test session."""
    if not HAS_PYQT5:
        pytest.skip("PyQt5 not installed")
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    created = False
    if app is None:
        app = QApplication(sys.argv[:1])
        created = True
    yield app
    if created:
        try:
            app.processEvents()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Isolated user data directory for license/entitlement tests.
# ---------------------------------------------------------------------------
@pytest.fixture
def isolated_user_data(tmp_path, monkeypatch):
    """
    Point utilities.license.get_user_data_dir() at a temporary directory so
    license/entitlement tests never touch the real %APPDATA% location.
    """
    fake_root = tmp_path / "MVC_Calculator"
    fake_root.mkdir(parents=True, exist_ok=True)

    def _fake_user_data_dir():
        return fake_root

    from utilities import license as license_mod
    monkeypatch.setattr(license_mod, "get_user_data_dir", _fake_user_data_dir)

    # Also patch utilities.entitlement copy (it re-imports get_user_data_dir)
    try:
        from utilities import entitlement as ent_mod
        monkeypatch.setattr(ent_mod, "get_user_data_dir", _fake_user_data_dir)
    except Exception:
        pass

    yield fake_root
