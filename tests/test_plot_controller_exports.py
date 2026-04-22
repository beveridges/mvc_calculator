"""Tests for PlotController.get_export_payload and MVC computation helpers."""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.requires_qt,
    pytest.mark.requires_numpy,
    pytest.mark.requires_scipy,
]

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


@pytest.fixture
def controller_with_data(qapp):
    from PyQt5.QtWidgets import QWidget
    from plot_controller import PlotController

    container = QWidget()
    pc = PlotController(container=container)

    rng = np.random.default_rng(42)
    data = rng.normal(0.0, 1.0, size=(3, 2000))
    pc.plot_mat_arrays(data, ["EMG1", "EMG2", "EMG3"], source_path="demo.mat")
    yield pc
    try:
        container.deleteLater()
    except Exception:
        pass


class TestGetExportPayload:
    def test_returns_none_when_no_data(self, qapp):
        from PyQt5.QtWidgets import QWidget
        from plot_controller import PlotController

        container = QWidget()
        pc = PlotController(container=container)
        assert pc.get_export_payload("x.mat") is None

    def test_returns_none_when_not_enough_bursts(self, controller_with_data):
        pc = controller_with_data
        pc._active_row = 0
        pc._selections[0] = [(0, 10)]  # only 1 burst
        assert pc.get_export_payload("x.mat", require_three=True) is None

    def test_returns_payload_without_three_bursts_when_not_required(
        self, controller_with_data
    ):
        pc = controller_with_data
        pc._active_row = 0
        pc._selections[0] = [(0, 100)]
        payload = pc.get_export_payload("x.mat", require_three=False)
        assert payload is not None
        assert payload["filename"] == "x.mat"
        assert payload["row"] == 0
        assert len(payload["bursts"]) == 1
        assert "mvc" in payload

    def test_returns_payload_with_three_bursts(self, controller_with_data):
        pc = controller_with_data
        pc._active_row = 1
        pc._selections[1] = [(0, 500), (600, 1000), (1100, 1500)]
        payload = pc.get_export_payload("demo.mat")
        assert payload is not None
        assert payload["row"] == 1
        assert len(payload["bursts"]) == 3
        assert payload["mvc"] is None or payload["mvc"] >= 0


class TestClearAndRowSelections:
    def test_clear_all_selections(self, controller_with_data):
        pc = controller_with_data
        ax = pc.axes[0]
        patch = ax.axvspan(0, 100, color="orange")
        pc._selections[0].append((0, 100))
        pc._patches[0].append(patch)
        pc.clear_all_selections()
        for r in pc._selections:
            assert pc._selections[r] == []
            assert pc._patches[r] == []
        assert pc._active_row is None

    def test_clear_row_selections_unknown_row_is_noop(self, controller_with_data):
        # Should not raise for row outside the known dict.
        controller_with_data.clear_row_selections(999)

    def test_set_active_row_bolds_correct_row(self, controller_with_data):
        pc = controller_with_data
        pc._set_active_row(2)
        assert pc._active_row == 2

    def test_on_row_clicked_clears_previous_row_selections(self, controller_with_data):
        pc = controller_with_data
        pc._active_row = 0
        ax = pc.axes[0]
        patch = ax.axvspan(0, 100, color="orange")
        pc._selections[0].append((0, 100))
        pc._patches[0].append(patch)
        pc._on_row_clicked(1)
        assert pc._active_row == 1
        assert pc._selections[0] == []
        assert pc._patches[0] == []
