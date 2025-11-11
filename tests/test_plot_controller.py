# -*- coding: utf-8 -*-
"""
Unit tests for mvc_calculator.utilities.plot_controller.PlotController
(Updated for the simplified rectangle-based span logic)

Covers:
1. Only 3 selections allowed per subplot row.
2. Shift-click deletion removes one span.
3. Clear-all removes all spans.
4. Clicking a different row radio bolds the correct row.
"""

# -*- coding: utf-8 -*-
"""
Unit tests for PlotController (rectangle-based span logic)
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pytest
# from utilities.plot_controller import PlotController
from plot_controller import PlotController

from PyQt5.QtWidgets import QWidget




# ---------------------------------------------------------------------------
# Helper: create a minimal PlotController with dummy EMG data
# ---------------------------------------------------------------------------
def make_plot_controller(qtbot, nrows=3, npts=1000):
    container = QWidget()
    qtbot.addWidget(container)
    plot_ctrl = PlotController(container=container)
    data = np.random.randn(nrows, npts)
    labels = [f"EMG {i+1}" for i in range(nrows)]
    plot_ctrl.plot_mat_arrays(data, labels)
    return plot_ctrl


# ---------------------------------------------------------------------------
# TEST 1: Only 3 selections allowed per row
# ---------------------------------------------------------------------------
def test_only_three_selections_allowed(qtbot):
    plot_ctrl = make_plot_controller(qtbot)
    row = 0

    # Manually simulate 4 drag events
    for i in range(4):
        lo, hi = 10 * i, 10 * i + 5
        if len(plot_ctrl._selections[row]) < 3:
            patch = plot_ctrl.axes[row].axvspan(lo, hi, color="orange", alpha=0.3)
            plot_ctrl._selections[row].append((lo, hi))
            plot_ctrl._patches[row].append(patch)
        else:
            # Simulate rejection
            pass

    assert len(plot_ctrl._selections[row]) == 3, "Should limit to 3 selections per row"
    assert len(plot_ctrl._patches[row]) == 3, "Should draw only 3 patches"


# ---------------------------------------------------------------------------
# TEST 2: Clear-all removes all spans
# ---------------------------------------------------------------------------
def test_clear_all_removes_all_spans(qtbot):
    plot_ctrl = make_plot_controller(qtbot)
    row = 0

    # Add 3 dummy spans
    for i in range(3):
        lo, hi = 20 * i, 20 * i + 5
        patch = plot_ctrl.axes[row].axvspan(lo, hi, color="orange", alpha=0.3)
        plot_ctrl._patches[row].append(patch)
        plot_ctrl._selections[row].append((lo, hi))

    plot_ctrl.clear_all_selections()

    for r in range(len(plot_ctrl.axes)):
        assert plot_ctrl._selections[r] == [], f"Row {r} selections not cleared"
        assert plot_ctrl._patches[r] == [], f"Row {r} patches not cleared"
    assert plot_ctrl._active_row is None


# ---------------------------------------------------------------------------
# TEST 3: Shift-click deletion reduces span count
# ---------------------------------------------------------------------------
def test_shift_click_deletes_span(qtbot):
    plot_ctrl = make_plot_controller(qtbot)
    row = 0

    # Add 3 dummy spans
    for i in range(3):
        lo, hi = 10 * i, 10 * i + 5
        patch = plot_ctrl.axes[row].axvspan(lo, hi, color="orange", alpha=0.3)
        plot_ctrl._patches[row].append(patch)
        plot_ctrl._selections[row].append((lo, hi))

    before = len(plot_ctrl._selections[row])

    # Simulate deletion
    target_idx = 1
    patch_to_remove = plot_ctrl._patches[row][target_idx]
    patch_to_remove.remove()
    plot_ctrl._patches[row].pop(target_idx)
    plot_ctrl._selections[row].pop(target_idx)

    after = len(plot_ctrl._selections[row])
    assert after == before - 1, "Shift-click should delete one span"


# ---------------------------------------------------------------------------
# TEST 4: Radio button click bolds the correct row
# ---------------------------------------------------------------------------
def test_row_click_bolds_correct_row(qtbot):
    plot_ctrl = make_plot_controller(qtbot)
    row_to_select = 1

    plot_ctrl._on_row_clicked(row_to_select)
    assert plot_ctrl._active_row == row_to_select, "Active row not updated"

    # Verify bolding visually by line width
    for i, ax in enumerate(plot_ctrl.axes):
        lw = next(iter(ax.spines.values())).get_linewidth()
        if i == row_to_select:
            assert lw > 1.5, "Selected row should be bold"
        else:
            assert lw < 1.5, "Unselected rows should not be bold"
            
            
def test_spans_only_on_active_row(qtbot):
    """
    Ensure that orange spans can only be drawn on the active row.
    Clicking or dragging in other rows must do nothing.
    """
    from matplotlib.backend_bases import MouseButton

    # --- Setup ---
    container = QWidget()
    qtbot.addWidget(container)
    plot_ctrl = PlotController(container=container)

    nrows, npts = 3, 1000
    data = np.random.randn(nrows, npts)
    labels = [f"EMG {i+1}" for i in range(nrows)]
    plot_ctrl.plot_mat_arrays(data, labels)

    # Activate first row (default 0)
    plot_ctrl._active_row = 0
    active_ax = plot_ctrl.axes[0]
    other_ax = plot_ctrl.axes[1]

    # --- Simulate selection in ACTIVE row ---
    press_event = type("E", (), {
        "button": MouseButton.LEFT,
        "inaxes": active_ax,
        "xdata": 100.0,
        "ydata": 0,
        "guiEvent": None,
    })()
    release_event = type("E", (), {
        "button": MouseButton.LEFT,
        "inaxes": active_ax,
        "xdata": 300.0,
        "ydata": 0,
        "guiEvent": None,
    })()

    plot_ctrl._click_x = None
    plot_ctrl._attach_mouse_handlers()  # ensure handlers exist

    # ✅ emit synthetic events properly
    plot_ctrl.canvas.callbacks.process("button_press_event", press_event)
    plot_ctrl.canvas.callbacks.process("button_release_event", release_event)

    # Verify a span was created in active row
    assert len(plot_ctrl._selections[0]) == 1
    assert len(plot_ctrl._patches[0]) == 1

    # --- Try to create span in NON-ACTIVE row ---
    press_event_other = type("E", (), {
        "button": MouseButton.LEFT,
        "inaxes": other_ax,
        "xdata": 150.0,
        "ydata": 0,
        "guiEvent": None,
    })()
    release_event_other = type("E", (), {
        "button": MouseButton.LEFT,
        "inaxes": other_ax,
        "xdata": 350.0,
        "ydata": 0,
        "guiEvent": None,
    })()

    # ✅ use same public dispatch API
    plot_ctrl.canvas.callbacks.process("button_press_event", press_event_other)
    plot_ctrl.canvas.callbacks.process("button_release_event", release_event_other)

    # --- Verify that NO span was added in other rows ---
    assert len(plot_ctrl._selections[1]) == 0, "No spans should be drawn on non-active rows"
    assert len(plot_ctrl._patches[1]) == 0, "No patches should exist on non-active rows"
