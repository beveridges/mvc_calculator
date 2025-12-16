# -*- coding: utf-8 -*-
# main.py
'''
Moviolabs download page.  
https://moviolabs.com/downloads/MVC_Calculator/releases/
USERNAME: imm.qtm.machine
PASSWORD: Nc)D6J(Fs1q+t=&x

USERNAME telemetry
PASSWORD: uGc84!qy~erQ?nlz
'''
from __future__ import print_function
import os, sys, time, logging, faulthandler
from logging.handlers import RotatingFileHandler
import xml.etree.ElementTree as ET
from datetime import datetime
import numpy as np


from telemetry.telemetry import log_startup, log_shutdown, log_event, log_error
from telemetry.perf_monitor import start_performance_monitor, stop_performance_monitor
from telemetry.notifier import record_launch_info, send_session_summary_email

from PyQt5.QtWidgets import QApplication, QMessageBox

# ============================================================
#  Startup banner — shown before anything else
# ============================================================
try:
    from utilities import version_info as v
    print(f"{v.FRIENDLYVERSIONNAME} {v.BUILDNUMBER}. Portable version.\nBuilding font cache - please wait...")
except Exception:
    print("MVC Calculator (version unknown). Portable version.")
print("-" * 60)

# ============================================================
#  Qt: import first so we can show the splash ASAP
# ============================================================
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPainter, QColor
from PyQt5.QtWidgets import (
    QSplashScreen, QMessageBox, QWidget, QVBoxLayout, QPushButton,
    QMenu, QAction, QFrame, QLabel, QFileDialog, QDialog, QLineEdit,
    QHBoxLayout, QTextEdit, QScrollArea
)



# --- Warm-up Matplotlib font cache in a background process ---
import subprocess, sys

def warmup_matplotlib_cache():
    """Run a tiny subprocess that imports matplotlib to force font cache build."""
    # CRITICAL: Skip subprocess warmup when running as frozen EXE to prevent infinite spawn
    if getattr(sys, "frozen", False):
        # When frozen, matplotlib will build its cache on first import anyway
        return
    try:
        subprocess.Popen(
            [sys.executable, "-c", "import matplotlib.pyplot as plt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

# Trigger font cache build asynchronously BEFORE heavy imports
warmup_matplotlib_cache()


# ============================================================
#  Heavy imports (now that splash is visible)
# ============================================================
import subprocess, urllib.request
from urllib.parse import urljoin

import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# -- CUSTOM ---------------------
from config.defaults import BEST_OF
from dialogs.load_mat_dialog import LoadMat
from processors.processors import Processor
from plot_controller import PlotController
import ui_initializer as gui
from utilities.version_info import (
    GITREVHEAD, BUILDNUMBER, VERSIONNUMBER, VERSIONNAME, FRIENDLYVERSIONNAME,
    GITTAG, CONDAENVIRONMENTNAME, PYTHONVERSION, CONDAENVIRONMENTFILENAME
)
from utilities.license import load_and_validate_license, find_license_file, get_license_file_path
from utilities.path_utils import base_path
from sbui.consoleui.console_output import SBConsoleOutput

# ============================================================
#  Logging (frozen-safe)
# ============================================================
if getattr(sys, "frozen", False):
    # Running as frozen EXE (PyInstaller) → use a writable user dir
    LOG_DIR = os.path.join(os.environ.get("APPDATA", os.getcwd()), "MVC_Calculator", "logs")
else:
    # Running from source (Spyder/dev)
    LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

os.makedirs(LOG_DIR, exist_ok=True)
LOGFILE = os.path.join(LOG_DIR, "mvc_calculator.log")

handler = RotatingFileHandler(LOGFILE, maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler, logging.StreamHandler(sys.stdout)]
)

# Fault handler
try:
    with open(LOGFILE, "a") as fh:
        faulthandler.enable(fh)
except Exception:
    faulthandler.enable()

def handle_uncaught_exception(exctype, value, tb):
    logging.critical("Uncaught exception", exc_info=(exctype, value, tb))
sys.excepthook = handle_uncaught_exception

# ============================================================
#  Splash progress helper
# ============================================================
def update_splash(splash, message, percent):
    """Update splash text safely (accepts splash instance)."""
    if splash is None:
        return
    splash.showMessage(f"{message}... {percent}%",
                       Qt.AlignBottom | Qt.AlignCenter,
                       Qt.black)
    QtWidgets.qApp.processEvents()




APP_VERSION = f"{FRIENDLYVERSIONNAME} {VERSIONNUMBER}.{BUILDNUMBER}"


# ============================================================
#  Main Window
# ============================================================
class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, splash=None):
        super(ApplicationWindow, self).__init__()
        self.splash = splash

        # Load UI
        self.ui_initializer = gui.setup(self, None)
        self._current_viewfinder = None

        # Console logger → QTextEdit/PlainText
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        self.logger = SBConsoleOutput(
            target=self.ledt_output,
            formatter=formatter,
            send_button=self.btn_sendLog,
            logfile=LOGFILE,
        )
        logging.info("=== Session started ===")

        QtCore.QTimer.singleShot(
            0, lambda: self.ledt_output.verticalScrollBar().setValue(
                self.ledt_output.verticalScrollBar().maximum()
            )
        )

        # UI elements
        self.form_btm_graph = self.findChild(QFrame, "form_btm_graph")
        self.placeholder_image = self.findChild(QLabel, "placeholder_image")
        if self.form_btm_graph is None:
            print("❌ form_btm_graph not found!")

        # Plot controller
        self.plot_controller = PlotController(
            parent=self,
            container=self.lbl_background,
            main_window=self
        )
        self.ui_initializer.plot_controller = self.plot_controller
        self.plot_controller.main_window = self
        self.main_window = self
        self.main_window.plot_controller = self.plot_controller

        self.myFigTop = self.plot_controller.canvas

        self.activateWindow()

        self.threadpool = QtCore.QThreadPool()
        logging.info('Multithreading with maximum %d threads', self.threadpool.maxThreadCount())

        # Version info
        logging.info(f"=== {FRIENDLYVERSIONNAME} executable started ===")
        logging.info(f"VERSIONNUMBER = {VERSIONNUMBER}")
        logging.info(f"BUILDNUMBER   = {BUILDNUMBER}")
        logging.info(f"GITREVHEAD    = {GITREVHEAD}")
        logging.info(f"VERSIONNAME   = {VERSIONNAME}")
        logging.info(f"GITTAG        = {GITTAG}")
        logging.info(f"CONDAENVIRONMENTNAME = {CONDAENVIRONMENTNAME}")
        logging.info(f"PYTHONVERSION = {PYTHONVERSION}")
        logging.info(f"CONDAENVIRONMENTFILENAME = {CONDAENVIRONMENTFILENAME or '(not found)'}")

        # Window basics
        self.setWindowFlag(Qt.WindowMaximizeButtonHint)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowTitle(FRIENDLYVERSIONNAME)
        self.setWindowIcon(QIcon(base_path('resources/icons', 'icn_emg.png')))

        # Buttons
        self.btn_loadMat.clicked.connect(self.load_mat_files)
        self.btn_exit.clicked.connect(self.close)
        self.btn_burstDetection.clicked.connect(self.on_burst_detection)

        self.btn_process.clicked.connect(self.on_process_clicked)
        self.btn_processBatch.clicked.connect(self.on_process_clicked_batch)
        self.btn_export.clicked.connect(self.export_mvc_xml)

        self.file_path = None

        # Tabs basic style (lightweight)
        self.tw_plotting.setStyleSheet("""
            QTabBar::tab { font-size: 13px; padding: 8px 16px; height: 15px; }
        """)
        self.tw_plotting.clear()
        self._enable_tab_context_menu()

    # ---------------- Tab context menu ----------------
    def _enable_tab_context_menu(self):
        tabbar = self.tw_plotting.tabBar()
        tabbar.setContextMenuPolicy(Qt.CustomContextMenu)
        tabbar.customContextMenuRequested.connect(self._on_tab_context_menu)

    def _on_tab_context_menu(self, pos):
        tabbar = self.tw_plotting.tabBar()
        index = tabbar.tabAt(pos)
        if index < 0:
            return

        menu = QMenu(self)
        close_action = QAction("Close Tab", self)
        close_action.triggered.connect(lambda _, i=index: self._close_tab(i))
        menu.addAction(close_action)
        menu.exec_(tabbar.mapToGlobal(pos))

    def _close_tab(self, index):
        tab_name = self.tw_plotting.tabText(index)
        widget = self.tw_plotting.widget(index)
        if widget:
            widget.deleteLater()
        self.tw_plotting.removeTab(index)
        self.ledt_output.appendPlainText(f"[info] Closed tab: {tab_name}")

    # ---------------- Helpers ----------------
    def _get_current_plot_and_row(self):
        """
        Return (plot_ctrl, row, signal) for current TAB/row or (None, None, None).
        """
        idx = self.tw_plotting.currentIndex()
        if idx < 0:
            self.ledt_output.appendPlainText("[warn] No tab selected")
            return None, None, None

        tab = self.tw_plotting.widget(idx)
        plot_ctrl = getattr(tab, "plot_ctrl", None)
        if plot_ctrl is None:
            self.ledt_output.appendPlainText("[warn] No plot controller on this tab")
            return None, None, None

        row = getattr(plot_ctrl, "_active_row", None)
        if row is None:
            self.ledt_output.appendPlainText("[warn] No active row selected")
            return None, None, None

        if plot_ctrl._data is None:
            self.ledt_output.appendPlainText("[warn] No data loaded in this PlotController")
            return None, None, None

        signal = plot_ctrl._data[row, :]
        return plot_ctrl, row, signal

    def on_clear_all_rows(self, plot_ctrl):
        """Clear selections from all rows in the given PlotController."""
        if not plot_ctrl:
            return
        for row in range(len(plot_ctrl.axes)):
            plot_ctrl.clear_row_selections(row)
        self.ledt_output.appendPlainText("[info] Cleared all selections in current tab")

    # ---------------- Data I/O ----------------
    def load_mat_files(self):
        dialog = LoadMat(self)
        dialog.matsImported.connect(self.on_mats_imported)
        dialog.exec_()

    def on_mats_imported(self, results):
        self.tw_plotting.clear()
        for res in results:
            base_name = os.path.basename(res["path"])
            tab = QWidget()
            layout = QVBoxLayout(tab)

            plot_ctrl = PlotController(parent=self, container=tab, main_window=self)
            layout.addWidget(plot_ctrl.toolbar)
            layout.addWidget(plot_ctrl.canvas)

            plot_ctrl.plot_mat_arrays(res["data"], res["labels"], source_path=res["path"])

            tab.plot_ctrl = plot_ctrl
            self.tw_plotting.addTab(tab, base_name)

    # ---------------- Burst detection ----------------
    def on_burst_detection(self):
        idx = self.tw_plotting.currentIndex()
        if idx < 0:
            self.ledt_output.appendPlainText("[warn] No plotting tab is selected.")
            return

        tab = self.tw_plotting.widget(idx)
        plot_ctrl = getattr(tab, "plot_ctrl", None)
        if plot_ctrl is None:
            self.ledt_output.appendPlainText("[warn] No plot controller on this tab.")
            return

        row = getattr(plot_ctrl, "_active_row", None)
        if row is None:
            self.ledt_output.appendPlainText("[warn] No active row selected.")
            return

        if plot_ctrl._data is None:
            self.ledt_output.appendPlainText("[warn] No data loaded in this PlotController")
            return

        signal = plot_ctrl._data[row, :]
        fs = globals().get("DEFAULT_SEMG_FREQUENCY", 2000)

        try:
            proc = Processor()
            energy_vec, _ = proc.energy_detection(signal, fs=fs)

            # clear old patches + selections for this row
            if row in plot_ctrl._patches:
                for patch in plot_ctrl._patches[row]:
                    try:
                        patch.remove()
                    except Exception:
                        pass
                plot_ctrl._patches[row] = []
            plot_ctrl._selections[row] = []

            # detect bursts
            bursts = []
            inside = False
            start = None
            for i, val in enumerate(energy_vec):
                if val == 1 and not inside:
                    start = i
                    inside = True
                elif val == 0 and inside:
                    bursts.append((start, i))
                    inside = False
            if inside:
                bursts.append((start, len(energy_vec)))

            fname = os.path.basename(plot_ctrl._source_path) if plot_ctrl._source_path else f"Tab {idx}"
            label = plot_ctrl._labels[row] if plot_ctrl._labels is not None else f"Row {row+1}"

            if bursts:
                self.ledt_output.appendPlainText(
                    f"[info] Burst detection for {fname}, {label}: {len(bursts)} bursts"
                )

                burst_vals = []
                for j, (lo, hi) in enumerate(bursts, 1):
                    seg = signal[int(lo):int(hi)]
                    if seg.size > 0:
                        # Use same MVC processing as the MVC calculation for consistency
                        mvc_val, _ = proc.mvc_matlab(seg)
                        val = float(mvc_val) if not np.isnan(mvc_val) else 0.0
                        burst_vals.append(val)

                        # draw new span
                        p = plot_ctrl.axes[row].axvspan(lo, hi, color="orange", alpha=0.30)
                        plot_ctrl._selections[row].append((lo, hi))
                        plot_ctrl._patches[row].append(p)

                        self.ledt_output.appendPlainText(f"   Burst {j}: {lo}–{hi} → {val:.2f}")

                if burst_vals:
                    avg_val = sum(burst_vals) / len(burst_vals)
                    max_val = max(burst_vals)
                    self.ledt_output.appendPlainText(f"   Average MVC value: {avg_val:.2f}")
                    self.ledt_output.appendPlainText(f"   Max MVC value: {max_val:.2f}")

                plot_ctrl.canvas.draw_idle()
            else:
                self.ledt_output.appendPlainText(f"[warn] No bursts detected for {fname}, {label}")

        except Exception as e:
            self.ledt_output.appendPlainText(f"[error] Burst detection failed: {e}")

    # ---------------- Selections ----------------
    def on_clear_selections(self):
        """Remove all selections from all subplots in the current tab."""
        idx = self.tw_plotting.currentIndex()
        if idx < 0:
            self.ledt_output.appendPlainText("[warn] No tab selected")
            return

        tab = self.tw_plotting.widget(idx)
        plot_ctrl = getattr(tab, "plot_ctrl", None)
        if plot_ctrl is None:
            self.ledt_output.appendPlainText("[warn] No plot controller in this tab")
            return

        for r in range(plot_ctrl._data.shape[0]):
            if r in plot_ctrl._patches:
                for patch in plot_ctrl._patches[r]:
                    try:
                        patch.remove()
                    except Exception:
                        pass
                plot_ctrl._patches[r] = []
            if r in plot_ctrl._selections:
                plot_ctrl._selections[r] = []

        plot_ctrl.canvas.draw_idle()
        self.ledt_output.appendPlainText("[info] Cleared all selections for this tab]")

    # ---------------- Export / Import XML ----------------
    def export_mvc_xml(self):
        savepath, _ = QFileDialog.getSaveFileName(self, "Export XML", "", "XML Files (*.xml)")
        if not savepath:
            logging.info("Export cancelled: no file path selected.")
            return

        session_data = []
        for i in range(self.tw_plotting.count()):
            tab = self.tw_plotting.widget(i)
            file_label = self.tw_plotting.tabText(i)
            plot_ctrl = getattr(tab, "plot_ctrl", None)
            if not plot_ctrl:
                continue

            payload = plot_ctrl.get_export_payload(file_label, require_three=False)
            if payload:
                session_data.append(payload)
                logging.info(
                    f"Prepared export: file={payload['filename']} row={payload['row']} "
                    f"bursts={len(payload['bursts'])} mvc={payload['mvc']}"
                )

        if not session_data:
            logging.info("Nothing to export (no selections on the active rows).")
            return

        root = ET.Element("MVCResults")
        now = datetime.now()
        info = ET.SubElement(root, "ExportInfo")
        ET.SubElement(info, "Date").text = now.strftime("%Y-%m-%d")
        ET.SubElement(info, "Time").text = now.strftime("%H:%M:%S")

        for f in session_data:
            fe = ET.SubElement(root, "File", name=f["filename"])
            ET.SubElement(fe, "Row").text = str(f["row"])
            if f["mvc"] is not None:
                ET.SubElement(fe, "MVC").text = str(f["mvc"])
            bursts = ET.SubElement(fe, "Bursts")
            for idx, (lo, hi) in enumerate(f["bursts"], 1):
                b = ET.SubElement(bursts, "Burst", id=str(idx))
                ET.SubElement(b, "Start").text = str(lo)
                ET.SubElement(b, "End").text = str(hi)

        ET.ElementTree(root).write(savepath, encoding="utf-8", xml_declaration=True)
        logging.info(f"XML export completed: {savepath}")

    def import_mvc_xml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import XML", "", "XML Files (*.xml)")
        if not path:
            return

        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception as e:
            self.ledt_output.appendPlainText(f"[error] Failed to read XML: {e}")
            return

        self.ledt_output.appendPlainText("=== Imported MVC XML ===")

        files = root.findall("File")
        if not files:
            self.ledt_output.appendPlainText("[warn] No <File> entries found.")
            self.ledt_output.appendPlainText("=== End of import ===")
            return

        max_len = max(len(f.attrib.get("name", "")) for f in files)
        tab_width = 8
        pad_tabs = lambda s: "\t" * max(1, (max_len - len(s)) // tab_width + 1)

        loaded_tab_names = [self.tw_plotting.tabText(i).strip() for i in range(self.tw_plotting.count())]

        for file_elem in files:
            fname = file_elem.attrib.get("name", "unknown").strip()
            row_text = file_elem.findtext("Row", default="?")
            mvc_text = file_elem.findtext("MVC", default="n/a")
            bursts_elem = file_elem.find("Bursts")

            burst_texts = []
            intervals = []
            if bursts_elem is not None:
                for b in bursts_elem.findall("Burst"):
                    lo = b.findtext("Start", default="?")
                    hi = b.findtext("End", default="?")
                    burst_texts.append(f"({lo}-{hi})")
                    try:
                        intervals.append((float(lo), float(hi)))
                    except ValueError:
                        pass

            bursts_str = ", ".join(burst_texts) if burst_texts else "no bursts"
            spacer = pad_tabs(fname)

            if fname in loaded_tab_names:
                tab_idx = loaded_tab_names.index(fname)
                tab = self.tw_plotting.widget(tab_idx)
                plot_ctrl = getattr(tab, "plot_ctrl", None)

                if plot_ctrl is not None and intervals:
                    row = int(row_text)
                    if row in plot_ctrl._selections:
                        plot_ctrl.clear_row_selections(row)
                    ax = plot_ctrl.axes[row]
                    for (lo, hi) in intervals:
                        patch = ax.axvspan(lo, hi, color="orange", alpha=0.3)
                        plot_ctrl._patches[row].append(patch)
                        plot_ctrl._selections[row].append((lo, hi))
                    plot_ctrl.canvas.draw_idle()

                    msg = (
                        f"[info] MATLAB MVC (imported)\n"
                        f"{fname}:{spacer}Row {row_text}: {mvc_text}\n"
                        f"bursts at: {bursts_str}"
                    )
                else:
                    msg = (
                        f"[info] MATLAB MVC (imported)\n"
                        f"{fname}:{spacer}Row {row_text}: {mvc_text}\n"
                        f"bursts at: {bursts_str} (not loaded in UI)"
                    )
            else:
                msg = (
                    f"[info] MATLAB MVC (imported)\n"
                    f"{fname}:{spacer}Row {row_text}: {mvc_text}\n"
                    f"bursts at: {bursts_str} (not loaded in UI)"
                )

            self.ledt_output.appendPlainText(msg)

        self.ledt_output.appendPlainText("=== End of import ===")

    # ---------------- Batch process ----------------
    def on_process_clicked(self):
        """Execute MATLAB-style MVC calculation for the current tab/row/selections."""
        idx = self.tw_plotting.currentIndex()
        if idx < 0:
            self.ledt_output.appendPlainText("[warn] No tab selected")
            return

        tab = self.tw_plotting.widget(idx)
        plot_ctrl = getattr(tab, "plot_ctrl", None)
        if plot_ctrl is None:
            self.ledt_output.appendPlainText("[warn] No PlotController found in this tab")
            return

        row = getattr(plot_ctrl, "_active_row", None)
        if row is None:
            self.ledt_output.appendPlainText("[warn] No active row selected")
            return

        if plot_ctrl._data is None:
            self.ledt_output.appendPlainText("[warn] No data loaded in this PlotController")
            return

        signal = plot_ctrl._data[row, :]
        selections = plot_ctrl._selections.get(row, [])

        if len(selections) < BEST_OF:
            self.ledt_output.appendPlainText(
                f"[warn] Not enough selections for MVC — need {BEST_OF}, found {len(selections)}."
            )
            return

        proc = Processor()
        mvc_values = []
        for (lo, hi) in selections[:BEST_OF]:
            segment = signal[int(lo):int(hi)]
            if segment.size > 0:
                mvc_val, rms_val = proc.mvc_matlab(segment)
                mvc_values.append(mvc_val)

        if not mvc_values:
            self.ledt_output.appendPlainText("[warn] No valid data in selected intervals.")
            return

        mvc_final = max(mvc_values)
        fname = os.path.basename(plot_ctrl._source_path) if plot_ctrl._source_path else f"Tab {idx}"
        label = plot_ctrl._labels[row] if plot_ctrl._labels is not None else f"Row {row+1}"
        msg = f"[info] MATLAB MVC (best of {BEST_OF})\nfor {fname}, {label}: {mvc_final:.3f}"
        self.ledt_output.appendPlainText(msg)

    def on_process_clicked_batch(self):
        """Run MVC batch across all tabs with ≥ BEST_OF selections."""
        total_tabs = self.tw_plotting.count()
        if total_tabs == 0:
            self.ledt_output.appendPlainText("[warn] No open tabs.")
            return

        self.ledt_output.appendPlainText("\n=== Batch MVC all open tabs ===")
        proc = Processor()
        any_processed = False

        for i in range(total_tabs):
            tab_name = self.tw_plotting.tabText(i)
            tab = self.tw_plotting.widget(i)
            plot_ctrl = getattr(tab, "plot_ctrl", None)

            if plot_ctrl is None or plot_ctrl._data is None:
                self.set_tab_alert(i, True)
                self.ledt_output.appendPlainText(f"[warn] {tab_name}: No data or plot controller.")
                continue

            row = getattr(plot_ctrl, "_active_row", None)
            if row is None:
                self.set_tab_alert(i, True)
                self.ledt_output.appendPlainText(f"[warn] {tab_name}: No active row selected.")
                continue

            selections = plot_ctrl._selections.get(row, [])
            if len(selections) < BEST_OF:
                self.set_tab_alert(i, True)
                self.ledt_output.appendPlainText(
                    f"[warn] {tab_name}: Not enough selections (found {len(selections)})."
                )
                continue

            self.set_tab_alert(i, False)

            signal = plot_ctrl._data[row, :]
            mvc_values = []
            for (lo, hi) in selections[:BEST_OF]:
                segment = signal[int(lo):int(hi)]
                if segment.size > 0:
                    mvc_val, _ = proc.mvc_matlab(segment)
                    mvc_values.append(mvc_val)

            if not mvc_values:
                self.ledt_output.appendPlainText(f"[warn] {tab_name}: No valid data in selections.")
                continue

            mvc_final = max(mvc_values)
            fname = os.path.basename(plot_ctrl._source_path) if plot_ctrl._source_path else tab_name
            label = plot_ctrl._labels[row] if plot_ctrl._labels is not None else f"Row {row+1}"

            plot_ctrl._mvc_result = mvc_final
            msg = f"[info] MVC for {fname}, {label}: {mvc_final:.3f}"
            self.ledt_output.appendPlainText(msg)
            any_processed = True

        if not any_processed:
            self.ledt_output.appendPlainText("[warn] No tabs had enough selections to process.")
        else:
            self.ledt_output.appendPlainText("=== End of batch MVC ===")

    # ---------------- Tab alert (red dot) ----------------
    def set_tab_alert(self, index: int, alert: bool):
        """Add or remove a red warning dot icon on the tab."""
        icon_size = 10
        if alert:
            pixmap = QPixmap(icon_size, icon_size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#ff4d4d"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, icon_size, icon_size)
            painter.end()

            icon = QIcon(pixmap)
            self.tw_plotting.setTabIcon(index, icon)
            self.tw_plotting.setIconSize(QSize(icon_size + 8, icon_size))  # spacing
        else:
            self.tw_plotting.setTabIcon(index, QIcon())


    def launch_about(self):
        QMessageBox.information(
        self,
        "About",
        f"{FRIENDLYVERSIONNAME}\nVersion {BUILDNUMBER}."
    )
    # ---------------- Help launcher -----------------
    def launch_help(self):
        """Open the MkDocs help site - ALWAYS opens user-guide, never index.html."""
        # Use base_path() for frozen EXE compatibility
        # ALWAYS open user-guide.html directly - NEVER show index.html
        site_index = base_path("docs_site", "site", "user-guide", "index.html")
        if not os.path.exists(site_index):
            # Do NOT fallback to index.html - show error instead
            QMessageBox.warning(
                self,
                "Help Not Available",
                f"This build does not include help files.\n\nExpected location:\n{site_index}"
            )
            return

        file_url = urljoin('file:', urllib.request.pathname2url(os.path.abspath(site_index)))
        try:
            if sys.platform.startswith("win"):
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if os.path.exists(chrome_path):
                    subprocess.Popen([chrome_path, file_url])
                else:
                    os.startfile(file_url)  # fallback
            else:
                subprocess.Popen(["xdg-open", file_url])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open browser:\n{e}")

    # ---------------- License Info Dialog ---------------- 
    def show_license_info(self):
        """Show dialog with HWID and license request information."""
        from pathlib import Path
        from utilities.license import get_machine_id, get_country, get_license_file_path
        
        # Get machine information
        hwid = get_machine_id()
        country = get_country() or "Unknown"
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Request License")
        dialog.setMinimumWidth(700)
        dialog.setMinimumHeight(600)
        dialog.resize(700, 700)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll.setWidget(content_widget)
        
        # Main dialog layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Title
        title = QLabel("Request License Key")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #3498db;")
        layout.addWidget(title)
        
        # Step-by-step instructions
        steps_label = QLabel("How to Request a License")
        steps_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #34495e; margin-top: 15px; margin-bottom: 8px;")
        layout.addWidget(steps_label)
        
        steps_text = QLabel(
            "<ol>"
            "<li><b>Copy the email template</b> below (it already includes your Hardware ID and Country)</li>"
            "<li><b>Paste it into your email client</b> and send it to support@moviolabs.com</li>"
            "<li><b>Wait for your license.key file</b> (you'll receive it as an email attachment)</li>"
            "<li><b>Download and save the license.key file</b> to one of the locations shown below</li>"
            "<li><b>Restart the application</b> to activate your license</li>"
            "</ol>"
        )
        steps_text.setWordWrap(True)
        steps_text.setStyleSheet("margin-left: 10px; margin-bottom: 15px;")
        layout.addWidget(steps_text)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Section header
        info_header = QLabel("Your Machine Information")
        info_header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #34495e; margin-top: 15px; margin-bottom: 8px;")
        layout.addWidget(info_header)
        
        info_note = QLabel(
            "<i>This information is automatically included in the email template below.</i>"
        )
        info_note.setWordWrap(True)
        info_note.setStyleSheet("margin-bottom: 10px; color: #666;")
        layout.addWidget(info_note)
        
        # HWID section (display only, not copyable)
        hwid_label = QLabel("Hardware ID (HWID)")
        hwid_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2c3e50; margin-top: 12px; margin-bottom: 5px;")
        layout.addWidget(hwid_label)
        
        hwid_explanation = QLabel(
            "This unique identifier is tied to your computer. Your license will only work on this machine."
        )
        hwid_explanation.setWordWrap(True)
        hwid_explanation.setStyleSheet("font-size: 9pt; color: #666; margin-bottom: 5px;")
        layout.addWidget(hwid_explanation)
        
        hwid_display = QLabel(f"<code style='font-family: Courier New; font-size: 10pt;'>{hwid}</code>")
        hwid_display.setStyleSheet("padding: 8px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 3px; margin-bottom: 10px;")
        hwid_display.setWordWrap(True)
        layout.addWidget(hwid_display)
        
        # Country section (display only, not copyable)
        country_label = QLabel("Country")
        country_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2c3e50; margin-top: 12px; margin-bottom: 5px;")
        layout.addWidget(country_label)
        
        country_explanation = QLabel(
            "Your license will be valid only in this country. This helps prevent unauthorized use."
        )
        country_explanation.setWordWrap(True)
        country_explanation.setStyleSheet("font-size: 9pt; color: #666; margin-bottom: 5px;")
        layout.addWidget(country_explanation)
        
        country_display = QLabel(f"<b style='font-size: 11pt;'>{country}</b>")
        country_display.setStyleSheet("padding: 8px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 3px; margin-bottom: 10px;")
        layout.addWidget(country_display)
        
        # Separator before email template
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # Email template section
        email_label = QLabel("Quick Email Template")
        email_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #34495e; margin-top: 15px; margin-bottom: 8px;")
        layout.addWidget(email_label)
        
        email_note = QLabel(
            "<i>You can copy this pre-filled email template and paste it into your email client.</i>"
        )
        email_note.setWordWrap(True)
        email_note.setStyleSheet("margin-bottom: 5px; color: #666;")
        layout.addWidget(email_note)
        
        email_template = f"""Subject: License Request for MVC Calculator

Hello,

I would like to request a license key for MVC Calculator.

Hardware ID: {hwid}
Country: {country}

Thank you!"""
        
        email_text = QTextEdit()
        email_text.setPlainText(email_template)
        email_text.setReadOnly(True)
        email_text.setMaximumHeight(150)
        email_text.setStyleSheet("font-family: 'Courier New', monospace; padding: 5px;")
        layout.addWidget(email_text)
        
        email_copy_btn = QPushButton("Copy Email Template")
        email_copy_btn.clicked.connect(lambda: self._copy_to_clipboard(email_template))
        layout.addWidget(email_copy_btn)
        
        # Separator before license location
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator3)
        
        # License file location info
        license_location_label = QLabel("Where to Save Your License Key")
        license_location_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #34495e; margin-top: 15px; margin-bottom: 8px;")
        layout.addWidget(license_location_label)
        
        location_instructions = QLabel(
            "<b>After receiving your license.key file via email:</b><br>"
            "1. Download the attached <b>license.key</b> file from the email<br>"
            "2. Save the file to one of the locations shown below (keep the exact filename)<br>"
            "3. Restart the application to activate your license"
        )
        location_instructions.setWordWrap(True)
        location_instructions.setStyleSheet("margin-bottom: 10px; margin-left: 10px;")
        layout.addWidget(location_instructions)
        
        # Recommended location (generic path - directory only)
        recommended_path = "%APPDATA%\\MVC_Calculator\\"
        recommended_label = QLabel("1. Recommended Location (persists across updates)")
        recommended_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #27ae60; margin-top: 12px; margin-bottom: 5px;")
        layout.addWidget(recommended_label)
        
        recommended_path_layout = QHBoxLayout()
        recommended_path_input = QLineEdit()
        recommended_path_input.setText(recommended_path)
        recommended_path_input.setReadOnly(True)
        recommended_path_input.setStyleSheet("font-family: 'Courier New', monospace; padding: 8px; background-color: #f5f5f5;")
        recommended_path_copy_btn = QPushButton("Copy Path")
        recommended_path_copy_btn.setStyleSheet("padding: 5px 15px;")
        recommended_path_copy_btn.clicked.connect(lambda: self._copy_to_clipboard(recommended_path))
        recommended_path_layout.addWidget(recommended_path_input)
        recommended_path_layout.addWidget(recommended_path_copy_btn)
        layout.addLayout(recommended_path_layout)
        
        # Legacy location (example path - directory only)
        legacy_path = "C:\\Program Files\\MVC_Calculator\\"
        legacy_label = QLabel("2. Alternative Legacy Location (example)")
        legacy_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e67e22; margin-top: 12px; margin-bottom: 5px;")
        layout.addWidget(legacy_label)
        
        legacy_path_display = QLabel(f"<code style='font-family: Courier New; font-size: 10pt;'>{legacy_path}</code>")
        legacy_path_display.setStyleSheet("padding: 8px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 3px; margin-bottom: 10px;")
        legacy_path_display.setWordWrap(True)
        layout.addWidget(legacy_path_display)

        # Portable version location (placeholder - directory only)
        portable_path = "<portable unzip folder>\\MVC_Calculator\\"
        portable_label = QLabel("3. Portable Version (example)")
        portable_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e67e22; margin-top: 12px; margin-bottom: 5px;")
        layout.addWidget(portable_label)

        portable_path_display = QLabel(f"<code style='font-family: Courier New; font-size: 10pt;'>{portable_path}</code>")
        portable_path_display.setStyleSheet("padding: 8px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 3px; margin-bottom: 10px;")
        portable_path_display.setWordWrap(True)
        layout.addWidget(portable_path_display)
        
        location_note = QLabel(
            "<b>Note:</b> Save the license.key file in one of these directories. "
            "The recommended location (%APPDATA%\\MVC_Calculator\\) persists across application updates. "
            "The legacy location (same directory as executable) and the portable unzip folder also work but may be lost during updates."
        )
        location_note.setWordWrap(True)
        location_note.setStyleSheet("margin-top: 5px; margin-bottom: 10px; padding: 8px; background-color: #e8f4f8; border-left: 3px solid #2196F3;")
        layout.addWidget(location_note)
        
        # Support info
        separator4 = QFrame()
        separator4.setFrameShape(QFrame.HLine)
        separator4.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator4)
        
        support_info = QLabel(
            f"<b style='font-size: 13pt;'>Need Help?</b><br>"
            f"Email: <a href='mailto:support@moviolabs.com' style='color: #3498db;'>support@moviolabs.com</a><br>"
            f"<i style='color: #7f8c8d;'>Include your Hardware ID and Country in your message.</i>"
        )
        support_info.setWordWrap(True)
        support_info.setOpenExternalLinks(True)
        support_info.setStyleSheet("margin-top: 15px; padding: 12px; background-color: #ecf0f1; border-radius: 5px; border-left: 4px solid #3498db;")
        layout.addWidget(support_info)
        
        # Close button (outside scroll area)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 20px; font-size: 10pt;")
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard and show confirmation."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Copied to clipboard!")

    # ---------------- Close/Cleanup ----------------
    def closeEvent(self, event):
        print("[INFO] Window is closing...")

        try:
            if hasattr(self, "update_timer") and self.update_timer:
                self.update_timer.stop()
        except Exception:
            pass

        try:
            if getattr(self, "is_recording", False) and hasattr(self, "camera") and self.camera:
                self.camera.stop_recording()
                self.is_recording = False
        except Exception:
            pass

        try:
            if hasattr(self, "camera") and self.camera:
                self.camera.stop()
        except Exception:
            pass
        finally:
            try:
                self.camera = None
            except Exception:
                pass

        try:
            if getattr(self, "_current_viewfinder", None):
                try:
                    host = getattr(self, "_vf_host", None)
                    if host and host.layout():
                        host.layout().removeWidget(self._current_viewfinder)
                except Exception:
                    pass
                self._current_viewfinder.hide()
                self._current_viewfinder.deleteLater()
                self._current_viewfinder = None
        except Exception:
            pass

        try:
            self.cleanUp()
        except Exception as e:
            print("Error during app cleanup:", e)
            logging.critical("Critical error during cleanUp()", exc_info=True)

        super().closeEvent(event)

    def cleanUp(self):
        logging.info("Starting application cleanup...")
        logging.shutdown()

# ============================================================
#  main() — reuse the already-created QApplication and splash
# ============================================================
def main():
    log_startup(APP_VERSION)
    record_launch_info(APP_VERSION)
    start_performance_monitor()

    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

        app = QtWidgets.QApplication(sys.argv)
        
        # License validation (only in frozen builds, must be after QApplication is created for dialogs)
        from utilities.license import ENFORCE_LICENSE
        if ENFORCE_LICENSE:
            license_file = find_license_file()
            if not license_file:
                license_path = get_license_file_path()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("License Required")
                msg.setText("License file not found")
                msg.setInformativeText(
                    f"Please place a valid license.key file in:\n\n"
                    f"{license_path}\n\n"
                    "This location persists across application updates.\n\n"
                    "Contact support@moviolabs.com for a license key.\n"
                    "Use Help → Request License... to get your Hardware ID."
                )
                msg.exec_()
                sys.exit(1)
            
            is_valid, error = load_and_validate_license()
            if not is_valid:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("License Validation Failed")
                msg.setText("Invalid License")
                msg.setInformativeText(
                    f"{error}\n\n"
                    "This license key is not valid for this machine or has expired.\n"
                    "Please contact support@moviolabs.com for assistance."
                )
                msg.exec_()
                sys.exit(1)
        # ---------- WSLg ICON FIX (safe, no variable shadowing) ----------
        import platform as _plat
        import os as _os
        from PyQt5 import QtGui
        from utilities.path_utils import resource_path
        
        _IN_WSL = (
            "microsoft" in _plat.uname().release.lower()
            or "WSL" in _os.getenv("WSL_DISTRO_NAME", "")
        )
        
        if _IN_WSL:
            print("Running inside WSL → applying WSLg icon fix")
        
            app.setApplicationName("MVC_Calculator")
            app.setDesktopFileName("mvc_calculator")
        
            app_icon = QtGui.QIcon(resource_path("resources/icons/icn_emg.png"))
            app.setWindowIcon(app_icon)
        else:
            print("Running on Windows → using normal icon logic")
        # -----------------------------------------------------------------

        splash_pix = QPixmap(base_path("resources/icons", "splash_zx_arr.png"))
        splash = QSplashScreen(splash_pix)
        splash.setFont(QFont("Helvetica", 10))
        splash.show()
        splash.showMessage("Initializing — please wait...", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
        app.processEvents()

        # progress ticks
        update_splash(splash, "LOADING RESOURCES", 10); time.sleep(0.05)
        update_splash(splash, "INITIALIZING COMPONENTS", 30); time.sleep(0.3)
        update_splash(splash, "TELEMETRÍA ACTIVADA", 40); time.sleep(0.7)
        update_splash(splash, "CONNECTING TO DB", 60); time.sleep(0.3)
        update_splash(splash, "STARTING INTERFACE", 90); time.sleep(0.05)

        window = ApplicationWindow(splash=splash)
        window.show()
        splash.showMessage("READY", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
        splash.finish(window)

        sys.exit(app.exec_())

    except Exception as e:
        log_error(e)
        raise

    finally:
        perf_summary = stop_performance_monitor()
        send_session_summary_email(APP_VERSION, perf_summary)
        log_shutdown()


# ============================================================
#  Entry point
# ============================================================
if __name__ == "__main__":
    main()
