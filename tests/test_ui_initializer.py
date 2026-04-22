"""Tests for ui_initializer.UIInitializer.

Creates a real ApplicationWindow-lite: a QMainWindow with stubbed slots that
UIInitializer connects its menu actions to.
"""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.requires_qt,
    pytest.mark.requires_numpy,
    pytest.mark.requires_scipy,
]


class _FakeMainWindow:
    """Placeholder; real tests use QMainWindow + test helpers below."""


@pytest.fixture
def main_window_with_slots(qapp):
    from PyQt5.QtWidgets import QMainWindow, QWidget

    class _MW(QMainWindow):
        def __init__(self):
            super().__init__()
            self.calls = []

        def load_mat_files(self): self.calls.append("load_mat_files")
        def import_mvc_xml(self): self.calls.append("import_mvc_xml")
        def export_mvc_xml(self): self.calls.append("export_mvc_xml")
        def launch_about(self): self.calls.append("launch_about")
        def show_license_info(self): self.calls.append("show_license_info")
        def launch_help(self): self.calls.append("launch_help")

    mw = _MW()
    yield mw
    try:
        mw.deleteLater()
    except Exception:
        pass


class TestUIInitializer:
    def test_sets_plot_controller_on_main_window(self, qapp, main_window_with_slots):
        from ui_initializer import UIInitializer
        from plot_controller import PlotController
        from PyQt5.QtWidgets import QWidget

        plot_ctrl = PlotController(container=QWidget())
        ui = UIInitializer(main_window_with_slots, plot_ctrl)
        assert main_window_with_slots.plot_controller is plot_ctrl
        assert ui.plot_controller is plot_ctrl

    def test_builds_menu_actions(self, qapp, main_window_with_slots):
        from ui_initializer import UIInitializer
        from plot_controller import PlotController
        from PyQt5.QtWidgets import QWidget

        plot_ctrl = PlotController(container=QWidget())
        UIInitializer(main_window_with_slots, plot_ctrl)
        mw = main_window_with_slots
        # All actions exist on the window
        for attr in [
            "load_MAT_action",
            "importXMLmot_action",
            "exportXMLmot_action",
            "exitAction",
            "aboutAction",
            "indexAction",
            "licenseInfoAction",
        ]:
            assert hasattr(mw, attr), attr

    def test_triggering_actions_calls_stubs(self, qapp, main_window_with_slots):
        from ui_initializer import UIInitializer
        from plot_controller import PlotController
        from PyQt5.QtWidgets import QWidget

        plot_ctrl = PlotController(container=QWidget())
        UIInitializer(main_window_with_slots, plot_ctrl)
        mw = main_window_with_slots

        mw.load_MAT_action.trigger()
        mw.importXMLmot_action.trigger()
        mw.exportXMLmot_action.trigger()
        mw.aboutAction.trigger()
        mw.licenseInfoAction.trigger()
        mw.indexAction.trigger()

        assert mw.calls == [
            "load_mat_files",
            "import_mvc_xml",
            "export_mvc_xml",
            "launch_about",
            "show_license_info",
            "launch_help",
        ]

    def test_setup_helper_returns_ui_initializer(self, qapp, main_window_with_slots):
        import ui_initializer as gui_mod
        from plot_controller import PlotController
        from PyQt5.QtWidgets import QWidget

        plot_ctrl = PlotController(container=QWidget())
        ui = gui_mod.setup(main_window_with_slots, plot_ctrl)
        assert isinstance(ui, gui_mod.UIInitializer)
