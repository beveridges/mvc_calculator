# -*- coding: utf-8 -*-
# main.py
from __future__ import print_function
from datetime import datetime
import faulthandler
import h5py
import logging
from logging.handlers import RotatingFileHandler
import math
import os
import numpy as np
import pandas as pd
import re
import scipy.io
import subprocess
from sys import argv
import sys
import traceback
import time
import win32com.client
import xml.etree.ElementTree as ET

import webbrowser

# sys.path.append(os.path.join(os.path.dirname(
#     __file__), 'dialogs'))  

# -- PYQT -----------------------
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QFileDialog, QLabel, QSplashScreen, QPlainTextEdit
from PyQt5.QtCore import Qt, QTimer, QElapsedTimer, pyqtSignal,  pyqtSlot, QThreadPool, QSize
from PyQt5.QtGui import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5 import uic
from PyQt5.QtGui import QFont, QIcon, QPixmap

import matplotlib.patches as patches
import matplotlib.patches as Rectangle
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon


# -- CUSTOM ---------------------
from dialogs.load_mat_dialog import LoadMat

from config.defaults import BEST_OF

from processors.processors import Processor

from plot_controller import PlotController
# from utilities.preferences import Preferences

import ui_initializer as gui
from utilities.version_info import (
    GITREVHEAD, BUILDNUMBER, VERSIONNUMBER, VERSIONNAME, FRIENDLYVERSIONNAME,
    GITTAG, CONDAENVIRONMENTNAME, PYTHONVERSION, CONDAENVIRONMENTFILENAME
)
from utilities.path_utils import resource_path
from utilities.path_utils import base_path
# from utilities.workers import Worker

from sbui.consoleui.console_output import SBConsoleOutput 
    
import xml.etree.ElementTree as ET
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog
import logging


if getattr(sys, "frozen", False):
    # Running as frozen exe → put application .log next to the .exe
    exe_dir = os.path.dirname(sys.executable)
else:
    # Running in Python (Spyder/dev) → put motus.log in CWD
    exe_dir = os.getcwd()



class LowercaseFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = record.levelname.lower()
        return super().format(record)


# --- Logging directories ---
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOGFILE = os.path.join(LOG_DIR, "mvc_calculator.log")

# --- Logging setup (file + console + rotation) ---
handler = RotatingFileHandler(LOGFILE, maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler, logging.StreamHandler(sys.stdout)]
)

# --- Fault + uncaught exception tracing ---
faulthandler.enable(open(LOGFILE, "a"))

def handle_uncaught_exception(exctype, value, tb):
    logging.critical("Uncaught exception", exc_info=(exctype, value, tb))

sys.excepthook = handle_uncaught_exception

# ---  Splash ---
def main():
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QtWidgets.QApplication(sys.argv)

    pixmap = QPixmap(base_path('resources/icons', 'mvccalculator_splash.png'))
    splash = QSplashScreen(pixmap)
    splash.show()
    font = QFont("Helvetica", 10)
    splash.setFont(font)

    delay = 0.1

    # === Simulate loading steps ===
    update_splash(splash, "LOADING RESOURCES", 10)
    time.sleep(delay)

    update_splash(splash, "INITIALIZING COMPONENTS", 30)
    time.sleep(delay)

    update_splash(splash, "CONNECTING TO DB", 60)
    time.sleep(delay)

    update_splash(splash, "STARTING INTERFACE", 90)
    time.sleep(delay)       

    update_splash(splash, "READY", 100)
    time.sleep(delay)

    splash.close()
    window = ApplicationWindow(splash=splash)
    window.show()

    sys.exit(app.exec_())


def update_splash(splash, message, percent):
    splash.showMessage(f"{message}... {percent}%",
                       QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter, QtCore.Qt.black)
    QtWidgets.qApp.processEvents()  


class ApplicationWindow(QtWidgets.QMainWindow):

    try:

        def __init__(self, splash=None):
            super(ApplicationWindow, self).__init__()
            self.splash = splash

            # Load the UI6
            self.ui_initializer = gui.setup(self, None)
                        
            self._current_viewfinder = None
                    
            
            # self.logger = SBConsoleOutput(self.ledt_output, formatter=formatter)
            
            # --- Formatter for console output ---
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            self.logger = SBConsoleOutput(
                target=self.ledt_output,
                formatter=formatter,
                send_button=self.btn_sendLog,  
                logfile=LOGFILE                 
            )
            logging.info("=== Session started ===")
            
    
            QtCore.QTimer.singleShot(0, lambda: self.ledt_output.verticalScrollBar().setValue(self.ledt_output.verticalScrollBar().maximum()))
                    
            # Now the UI is loaded, widgets like form_btm_graph exist
            self.form_btm_graph = self.findChild(QFrame, "form_btm_graph")
            self.placeholder_image = self.findChild(
                QLabel, "placeholder_image")

            if self.form_btm_graph is None:
                print("❌ form_btm_graph not found!")
            # if self.placeholder_image is None:
            #     print("❌ placeholder_image not found!")

            # Instantiate PlotController once
            self.plot_controller = PlotController(
                parent=self,
                container=self.lbl_background,
                main_window=self)

            # 3. Share plot_controller back into initializer + main_window
            self.ui_initializer.plot_controller = self.plot_controller
            # (optional: if PlotController expects mw reference)
            # self.plot_controller.mw = self
            self.plot_controller.main_window = self  # (if needed)
            self.main_window = self  # (optional, to keep naming consistent)
            self.main_window.plot_controller = self.plot_controller

            # 4. Safe to bind UI controls
            # self.plot_controller.bind_ui_controls()
            
            
            self.myFigTop = self.plot_controller.canvas 
    
            self.activateWindow()
            
            self.threadpool = QThreadPool()
            logging.info('Multithreading with maximum %d threads' %
                  self.threadpool.maxThreadCount())
                                    
            logging.info(f"=== {FRIENDLYVERSIONNAME} executable started ===")
            logging.info(f"VERSIONNUMBER = {VERSIONNUMBER}")
            logging.info(f"BUILDNUMBER   = {BUILDNUMBER}")
            logging.info(f"GITREVHEAD    = {GITREVHEAD}")
            logging.info(f"VERSIONNAME   = {VERSIONNAME}")
            logging.info(f"GITTAG        = {GITTAG}")
            logging.info(f"CONDAENVIRONMENTNAME = {CONDAENVIRONMENTNAME}")
            logging.info(f"PYTHONVERSION = {PYTHONVERSION}")
            logging.info(f"CONDAENVIRONMENTFILENAME = {CONDAENVIRONMENTFILENAME or '(not found)'}")

            self.setWindowFlag(Qt.WindowMaximizeButtonHint)
            self.setWindowFlag(Qt.WindowMinimizeButtonHint)
            self.setWindowTitle(FRIENDLYVERSIONNAME)
            self.setWindowIcon(QIcon(base_path('resources/icons', 'icn_emg.png')))

            # self.showMaximized()

            # self.prefs = Preferences()  
            # self.load_preferences()


            self.btn_loadMat.clicked.connect(self.load_mat_files) 
            self.btn_exit.clicked.connect(self.close) 
            
            self.btn_burstDetection.clicked.connect(self.on_burst_detection)
            
            # inside ApplicationWindow.__init__ after UI setup
            self.btn_process.clicked.connect(self.on_process_clicked)
            self.btn_processBatch.clicked.connect(self.on_process_clicked_batch)
            self.btn_export.clicked.connect(self.export_mvc_xml)


            # self.btn_process.clicked.connect(self.run_mvc_calculation)

            self.file_path = None
                
            self.tw_plotting.setStyleSheet("""
                QTabBar::tab {
                    font-size: 13px;
                    padding: 8px 16px;
                    height: 15px;
                }
            """)
            self.tw_plotting.clear()
            
            self._enable_tab_context_menu()

        def _enable_tab_context_menu(self):
            """Enable right-click context menu on tabs to close them."""
            tabbar = self.tw_plotting.tabBar()
            tabbar.setContextMenuPolicy(Qt.CustomContextMenu)
            tabbar.customContextMenuRequested.connect(self._on_tab_context_menu)
        
        def _on_tab_context_menu(self, pos):
            """Show context menu with 'Close Tab' when right-clicking a tab."""
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
            """Close the tab at the given index, showing its name in the console."""
            tab_name = self.tw_plotting.tabText(index)
            widget = self.tw_plotting.widget(index)
            if widget:
                widget.deleteLater()
            self.tw_plotting.removeTab(index)
            self.ledt_output.appendPlainText(f"[info] Closed tab: {tab_name}")
        
        
        def _get_current_plot_and_row(self):
            '''
            INTERNAL/PRIVATE METHOD _
            HELPER: Finds the current TAB, subplot, and numpay array for processing.
            Return (plot_ctrl, row, signal) for the current TAB/row or (None, None, None).
            '''
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
            self.ledt_output.appendPlainText(
                "[info] Cleared all selections in current tab"
            )

                
        def _style_tabs_for_plotting(self):
            plot_blue = "#3daee9"   # your plot color
            sel_bg    = "#d6f1fe"   # lighter blue for selected tab
            hover_bg  = "#eaf7ff"   # subtle hover
            base_bg   = "#f6f8fb"   # unselected tab background
            border    = "#cfd6e6"   # neutral border
        
            qss = f"""
            QTabWidget::pane {{
                border: 1px solid {plot_blue};
                border-top: 2px solid {plot_blue};
                background: white;
                top: -1px; /* tight seam with tabs */
            }}
        
            /* Base tab look */
            QTabBar::tab {{
                background: {base_bg};
                color: #1f2937;
                border: 1px solid {border};
                border-bottom-color: transparent; /* blend into pane */
                padding: 6px 16px;
                margin: 2px 2px 0 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-height: 26px;
                font-size: 14px;
                font-weight: 500;              
            }}
        
            /* Selected/current tab */
            QTabBar::tab:selected {{
                background: {sel_bg};
                color: #0b3d57;
                font-weight: 600;
                border: 1px solid {plot_blue};
                border-bottom-color: {sel_bg}; /* hide seam */
            }}
        
            /* Hover (not selected) */
            QTabBar::tab:hover:!selected {{
                background: {hover_bg};
                border-color: {plot_blue};
            }}
        
            /* Make the selected tab visually “on top” */
            QTabBar::tab:selected {{
                z-index: 2;
            }}
        
            /* Optional: disabled tabs look muted */
            QTabBar::tab:disabled {{
                color: #9aa4b2;
            }}
            """
        
            self.tw_plotting.setStyleSheet(qss)
            
            # inside ApplicationWindow.__init__ after other buttons
            self.btn_clearSelections = QPushButton("Clear Selections")
            self.btn_clearSelections.setCheckable(False)
            self.btn_clearSelections.setFixedHeight(self.btn_burstDetection.height())  # same height
            self.btn_clearSelections.setStyleSheet(self.btn_burstDetection.styleSheet())  # reuse style
            self.btn_clearSelections.clicked.connect(self.on_clear_selections)
            
            # Add it next to your other buttons
            self.buttonLayout.addWidget(self.btn_clearSelections)


                
            # self.btn_one_button.setIcon(
            #     QIcon(base_path('resources/icons', 'icn_movella_to_joint_angle.png')))
            # self.btn_one_button.setIconSize(QSize(256, 95))
            # self.btn_pmsystem.setIcon(
            #     QIcon(base_path('resources/icons', 'icn_patient_db_thin.png')))
            # self.btn_pmsystem.setIconSize(QSize(240, 55))

            # with QtCore.QSignalBlocker(self.tgl_arriba_rDa):
            #     self.tgl_arriba_rDa.setChecked(True)
            # with QtCore.QSignalBlocker(self.tgl_abajo_rDa):
            #     self.tgl_abajo_rDa.setChecked(True)

            # if not os.path.isdir('./datos/'):
            #     os.mkdir('./datos/')
            #     print("./datos/ directory does not exist. Creating it ... ")
            # self.fullFilePath = './datos/'

            # self._graficando_variables_.setEnabled(False)
            # self._graficando_variables_.setStyleSheet(
            #     "QGroupBox::title{ color: gray }")
            # self._graficando_tab_.setEnabled(False)
            # self._limites_de_eje_.setEnabled(False)
            # self._limites_de_eje_.setStyleSheet(
            #     "QGroupBox::title{ color: gray }")
            # self._limites_de_rango_.setEnabled(False)
            # self._limites_de_rango_.setStyleSheet(
            #     "QGroupBox::title{ color: gray }")


            # self.tabWidgetRight.setTabIcon(self.tabWidgetRight.indexOf(self.tabWebcam), QtGui.QIcon("artwork/icons/camera_deactivated.png"))

            # # self.toggle_graficando_anotaciones(False)

            # self.setup_camera_dropdown()
            # # self.setup_fps_dropdown()

            # self.webcam_started = False
            # # self.labelWebcamFeed.mousePressEvent = self.label_webcam_clicked

            # self.pushButtonRecord.clicked.connect(
            #     self.on_record_button_clicked)
            # self.pushButtonStop.clicked.connect(self.on_stop_button_clicked)

            # # In your constructor:
            # self.elapsed_timer = QElapsedTimer()
            # self.update_timer = QTimer(self)
            # self.update_timer.setInterval(1000)  # update every second

            # # Connect the QTimer to the update method
            # self.update_timer.timeout.connect(self.update_elapsed_label)

            # # Make sure label starts at 00:00:00
            # self.labelElapsedTime.setText("00:00:00")

            # # self.recordings_dir = base_path("video")
            # self.recordings_dir = get_recordings_dir()
            # # os.makedirs(self.recordings_dir, exist_ok=True)
            # # self.pushButtonStop.setEnabled(False)

            # self.is_recording = False
            # self.camera_ready = False

            # self.camera = None  # ✅ Prevent AttributeError

            # # self.btn_desactivar_la_camera.clicked.connect(
            # #     self.on_camera_deactivate_clicked) 
            # # self.btn_desactivar_la_camera.clicked.connect(
            # #     self.toggle_camera)
            
            
            # self.btn_desactivar_la_camera.clicked.connect(self.on_toggle_preview)

            # webcam_deactivated_icon_path = resource_path(
            #     "icons", "camera_deactivated.png")
            # tab_index = self.tabWidgetRight.indexOf(self.tabWebcam)
            # self.tabWidgetRight.setTabIcon(
            #     tab_index, QIcon(webcam_deactivated_icon_path))

            # self.btn_one_button.clicked.connect(self.one_button_click)
            # self.btn_pmsystem.clicked.connect(self.btn_pmsystem_click)

            # # self.cbx_frequencia_de_imagen.currentTextChanged.connect(
            # #     self.on_fps_pref_changed)

            # hide = self.prefs.get(
            #     "General", "hide_experimental", fallback="True") == "True"
            # self.apply_experimental_visibility(hide)

# %% PRE     
        # def eventFilter(self, obj, ev):
        #     if getattr(self, "_vf_host", None) and obj is self._vf_host and ev.type() == QtCore.QEvent.Resize and hasattr(self, "_rec_dot"):
        #         self._rec_dot.move(obj.width() - 22, 8)
        #     return super().eventFilter(obj, ev)
# %% MAIN
            

        def clear_tabs(self):
            self.tw_plotting.clear()
            self.file_path = None
        
        def export_mvc_xml(self):
            savepath, _ = QFileDialog.getSaveFileName(
                self, "Export XML", "", "XML Files (*.xml)"
            )
            if not savepath:
                logging.info("Export cancelled: no file path selected.")
                return
        
            session_data = []
            for i in range(self.tw_plotting.count()):
                tab = self.tw_plotting.widget(i)
                file_label = self.tw_plotting.tabText(i)   # e.g., original MAT filename
                plot_ctrl = getattr(tab, "plot_ctrl", None)
                if not plot_ctrl:
                    continue
        
                # Pull selections from the CURRENTLY CHECKED row
                # payload = plot_ctrl.get_export_payload_active_row(file_label, require_three=False)
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
  
           
        def get_active_row_data(self):
            if self._data is None:
                return None
            row = getattr(self, "_active_row", 0)
            if row < 0 or row >= self._data.shape[0]:
                return None
            return self._data[row, :]
   
        def import_mvc_xml(self):
            """
            Import a previously exported MVC XML file and display its contents
            with alignment. If the corresponding .mat file is loaded in a tab,
            the bursts will be plotted on that tab automatically.
            """
            from xml.etree import ElementTree as ET
            import os
        
            path, _ = QFileDialog.getOpenFileName(
                self, "Import XML", "", "XML Files (*.xml)"
            )
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
        
            # Longest filename → for nice alignment
            max_len = max(len(f.attrib.get("name", "")) for f in files)
            tab_width = 8
            pad_tabs = lambda s: "\t" * max(1, (max_len - len(s)) // tab_width + 1)
        
            # --- Get list of currently loaded tab names
            loaded_tab_names = [
                self.tw_plotting.tabText(i).strip() for i in range(self.tw_plotting.count())
            ]
        
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
                        # store numeric ranges for plotting
                        try:
                            intervals.append((float(lo), float(hi)))
                        except ValueError:
                            pass
        
                bursts_str = ", ".join(burst_texts) if burst_texts else "no bursts"
                spacer = pad_tabs(fname)
        
                # --- Find if this file is currently loaded in a tab
                if fname in loaded_tab_names:
                    tab_idx = loaded_tab_names.index(fname)
                    tab = self.tw_plotting.widget(tab_idx)
                    plot_ctrl = getattr(tab, "plot_ctrl", None)
        
                    if plot_ctrl is not None and intervals:
                        row = int(row_text)
                        if row in plot_ctrl._selections:
                            # clear any previous selections
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



   
        def launch_help(self):
            """Force open the MkDocs help site in Microsoft Chrome """
            import os, subprocess, sys, urllib.request
            from urllib.parse import urljoin
            from PyQt5.QtWidgets import QMessageBox
        
            site_index = os.path.join(os.path.dirname(__file__), "docs_site", "site", "index.html")
        
            if not os.path.exists(site_index):
                QMessageBox.warning(
                    self,
                    "Help not found",
                    f"Cannot find MkDocs help site at:\n{site_index}\n\n"
                    "Run:\n\n    mkdocs build\n\n"
                    "to generate it."
                )
                return
        
            file_url = urljoin('file:', urllib.request.pathname2url(os.path.abspath(site_index)))
        
            # --- Force open in Edge ---
            try:
                if sys.platform.startswith("win"):
                    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

                    if not os.path.exists(chrome_path):
                        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

                    if os.path.exists(chrome_path):
                        subprocess.Popen([chrome_path, file_url])
                    else:
                        os.startfile(file_url)  # fallback
                else:
                    subprocess.Popen(["xdg-open", file_url])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open browser:\n{e}")
   
         
        def load_mat_files(self):
             dialog = LoadMat(self)
             dialog.matsImported.connect(self.on_mats_imported)
             dialog.exec_()
   

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
                from processors.processors import Processor
                proc = Processor()
                energy_vec, _ = proc.energy_detection(signal, fs=fs)
        
                # --- clear old patches + selections for this row ---
                if row in plot_ctrl._patches:
                    for patch in plot_ctrl._patches[row]:
                        try:
                            patch.remove()
                        except Exception:
                            pass
                    plot_ctrl._patches[row] = []
                plot_ctrl._selections[row] = []
        
                # --- detect bursts ---
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
                            val = float(seg.max())
                            burst_vals.append(val)
        
                            # draw new span
                            p = plot_ctrl.axes[row].axvspan(lo, hi, color="orange", alpha=0.30)
                            plot_ctrl._selections[row].append((lo, hi))
                            plot_ctrl._patches[row].append(p)
        
                            self.ledt_output.appendPlainText(f"   Burst {j}: {lo}–{hi} → {val:.2f}")
        
                    if burst_vals:
                        avg_val = sum(burst_vals) / len(burst_vals)
                        self.ledt_output.appendPlainText(f"   Average value: {avg_val:.2f}")
        
                    plot_ctrl.canvas.draw_idle()
                else:
                    self.ledt_output.appendPlainText(f"[warn] No bursts detected for {fname}, {label}")
        
            except Exception as e:
                self.ledt_output.appendPlainText(f"[error] Burst detection failed: {e}")

        
        def on_clear_selections(self):
            """Remove all burst/manual selections from all subplots in the current tab."""
            idx = self.tw_plotting.currentIndex()
            if idx < 0:
                self.ledt_output.appendPlainText("[warn] No tab selected")
                return
        
            tab = self.tw_plotting.widget(idx)
            plot_ctrl = getattr(tab, "plot_ctrl", None)
            if plot_ctrl is None:
                self.ledt_output.appendPlainText("[warn] No plot controller in this tab")
                return
        
            # remove patches from all rows
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
            self.ledt_output.appendPlainText("[info] Cleared all selections for this tab")


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
        
                # ✅ Attach plot_ctrl to the tab
                tab.plot_ctrl = plot_ctrl
        
                self.tw_plotting.addTab(tab, base_name)

        def on_process_clicked(self):
            """Execute MATLAB-style MVC calculation for the current tab, selected row, and current selections."""
            idx = self.tw_plotting.currentIndex()
            if idx < 0:
                self.ledt_output.appendPlainText("[warn] No tab selected")
                return
        
            tab = self.tw_plotting.widget(idx)
            plot_ctrl = getattr(tab, "plot_ctrl", None)
            if plot_ctrl is None:
                self.ledt_output.appendPlainText("[warn] No PlotController found in this tab")
                return
        
            # Active row check
            row = getattr(plot_ctrl, "_active_row", None)
            if row is None:
                self.ledt_output.appendPlainText("[warn] No active row selected")
                return
        
            # Get EMG data for that row
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
        
            # Use only the selected intervals
            from processors.processors import Processor
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
            """
            Run MATLAB MVC calculation on all open tabs that have ≥ BEST_OF selections.
            Tabs missing selections are colored red as a reminder.
            Results appear in the console and are saved into plot_ctrl._mvc_result
            so they will be included in XML export.
            """
            total_tabs = self.tw_plotting.count()
            if total_tabs == 0:
                self.ledt_output.appendPlainText("[warn] No open tabs.")
                return
        
            self.ledt_output.appendPlainText("\n=== MVC all open tabs ===")
        
            proc = Processor()
            any_processed = False
        
            for i in range(total_tabs):
                tab_name = self.tw_plotting.tabText(i)
                tab = self.tw_plotting.widget(i)
                plot_ctrl = getattr(tab, "plot_ctrl", None)
        
                # Skip invalid tabs
                if plot_ctrl is None or plot_ctrl._data is None:
                    # self.tw_plotting.setTabTextColor(i, Qt.red)
                    self.set_tab_alert(i, True)
                    self.ledt_output.appendPlainText(f"[warn] {tab_name}: No data or plot controller.")
                    continue
        
                row = getattr(plot_ctrl, "_active_row", None)
                if row is None:
                    # self.tw_plotting.setTabTextColor(i, Qt.red)
                    self.set_tab_alert(i, True)
                    self.ledt_output.appendPlainText(f"[warn] {tab_name}: No active row selected.")
                    continue
        
                selections = plot_ctrl._selections.get(row, [])
                if len(selections) < BEST_OF:
                    # self.tw_plotting.setTabTextColor(i, Qt.red)
                    self.set_tab_alert(i, True)
                    self.ledt_output.appendPlainText(
                        f"[warn] {tab_name}: Not enough selections (found {len(selections)})."
                    )
                    continue
        
                # --- Valid tab: reset color to default ---
                # self.tw_plotting.setTabTextColor(i, Qt.black)
                self.set_tab_alert(i, False) 
        
                # Perform MVC across the selected intervals
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
        
                # ✅ Store MVC result in the PlotController for XML export
                plot_ctrl._mvc_result = mvc_final
        
                # ✅ Optional: if you have a per-row data structure, you can store it there too:
                # plot_ctrl._mvc_per_row[row] = mvc_final
        
                msg = f"[info] MVC for {fname}, {label}: {mvc_final:.3f}"
                self.ledt_output.appendPlainText(msg)
                any_processed = True
        
            if not any_processed:
                self.ledt_output.appendPlainText("[warn] No tabs had enough selections to process.")
            else:
                self.ledt_output.appendPlainText("=== End of batch MVC ===")

               
        def on_mat_files_selected(self, files):
            self.tw_plotting.clear()
            for file_path in files:
                base_name = os.path.basename(file_path)
        
                # Create a tab
                tab = QWidget()
                tab_layout = QVBoxLayout(tab)
        
                # Create a new PlotController for this tab
                plot_ctrl = PlotController(parent=self, container=tab, main_window=self)
                tab.plot_ctrl = plot_ctrl
        
                # Show toolbar + canvas
                plot_ctrl.canvas.setVisible(True)
                plot_ctrl.toolbar.setVisible(True)
                tab_layout.addWidget(plot_ctrl.toolbar)
                tab_layout.addWidget(plot_ctrl.canvas)
        
                # Add the Clear All Rows button at the bottom
                btn_clear_all = QPushButton("Clear All Rows")
                btn_clear_all.setFixedHeight(28)
                btn_clear_all.setStyleSheet("font-size: 12px; font-weight: bold;")
                btn_clear_all.clicked.connect(lambda _, pc=plot_ctrl: self.on_clear_all_rows(pc))
                tab_layout.addWidget(btn_clear_all, 0, alignment=Qt.AlignRight)
        
                # Load and plot the .mat file
                plot_ctrl.plot_mat_file(file_path)
        
                # Add the tab
                self.tw_plotting.addTab(tab, base_name)
                
                
        def set_tab_alert(self, index: int, alert: bool):
            """
            Add or remove a red warning dot icon on the tab, with spacing before text.
            Works across all platforms.
            """
            icon_size = 10
        
            if alert:
                # Create red dot
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
        
                # --- Add spacing between icon and text ---
                self.tw_plotting.setIconSize(QSize(icon_size + 8, icon_size))  # adds 8px spacing
            else:
                self.tw_plotting.setTabIcon(index, QIcon())  # clear icon





                
       

# %% PROGRAM CLOSE

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
                self.camera = None
        
            # Leave the host in the layout; just switch to placeholder and delete the viewfinder
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
        
            # self._show_webcam_placeholder("Cámara desactivada.")
        
            try:
                self.cleanUp()
            except Exception as e:
                print("Error during app cleanup:", e)
                logging.critical("Critical error during cleanUp()", exc_info=True)
        
            super().closeEvent(event)

# %% PROGRAM CLEANUP

        def cleanUp(self):
            logging.info("Starting application cleanup...")
            logging.shutdown()

            # # === Disconnect Bluetooth Socket ===
            # try:
            #     self.socket.disconnectFromService()
            #     logging.info("Bluetooth disconnected.")
            # except Exception as e:
            #     print("No Bluetooth connected. Closing...")
            #     logging.info(f"No Bluetooth connection to close: {e}")

            # # === Close Video Device ===
            # try:
            #     self.record_video.close_camera()
            #     logging.info("Video device closed.")
            # except Exception as e:
            #     print("No video device connected. Closing...")
            #     logging.info(f"No video device connected to close: {e}")
            # print("[INFO] Safe shutdown complete.")

    #  def cleanUp(self):
    #       logging.shutdown()
    #        try:
    #             self.socket.disconnectFromService()
    #         except:
    #             print("No bluetooth connected.      Closing...")
    #             logging.info("No bluetooth connected.      Closing...")

    #         try:
    #             self.record_video.close_camera()
    #         except:
    #             print("No video device connected.  Closing...")
    #             logging.info("No video device connected.  Closing...")

    #         try:
    #             if (os.path.exists(self.fullFilePath + self.participant_name + "_" + self.sessionSaveName + ".csv")):
    #                 print("IMU data was saved.  Closing...")
    #                 logging.info("IMU data was saved..  Closing...")
    #             else:
    #                 try:
    #                     self.write_btdata_csv()
    #                     # There is something to save - not just an empty file.
    #                     if (len(self.ax) > 1):
    #                         self.write_btdata_csv()
    #                         self.record_video.close_camera()
    #                 except:
    #                     print("No IMU data to save.  Closing...")
    #                     logging.info("No IMU data.  Closing...")
    #         except:
    #             print("No IMU data.  Closing...")
    #             logging.info("No IMU data.  Closing...")

    #         try:
    #             if (os.path.exists(self.fullFilePath + self.participant_name + "_" + self.sessionSaveName + "_videoWallTS.csv") or
    #                 os.path.exists(self.fullFilePath + self.participant_name + "_" + self.sessionSaveName + "_videoElapTS.csv") or
    #                     os.path.exists(self.fullFilePath + self.participant_name + "_" + self.sessionSaveName + "_videoLogfile.csv")):
    #                 print("Wallclock, elapsed, and log file data saved")
    #                 logging.info("Wallclock, elapsed, and log file data saved")
    #             else:
    #                 try:
    #                     if (len(self.record_video.videoTimestampsElapsed) > 1):
    #                         self.record_video.write_vTimestamps_csv()

    #                 except:
    #                     print("No timestamp data to save.  Closing...")
    #                     logging.info("No timestamp data to save.  Closing...")
    #         except:
    #             print("No timestamp data.  Closing...")
    #             logging.info("No timestamp data.  Closing...")

    except Exception as err:
        logging.critical(err)
        print(err)
        logging.shutdown()


if __name__ == "__main__":
    main()
