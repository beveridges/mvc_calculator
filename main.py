# -*- coding: utf-8 -*-
# main.py
from __future__ import print_function
from datetime import datetime
import faulthandler
import h5py
import logging
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
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# -- CUSTOM ---------------------
from dialogs.load_mat_dialog import LoadMat
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

if getattr(sys, "frozen", False):
    # Running as frozen exe → put motus.log next to the .exe
    exe_dir = os.path.dirname(sys.executable)
else:
    # Running in Python (Spyder/dev) → put motus.log in CWD
    exe_dir = os.getcwd()

class LowercaseFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = record.levelname.lower()
        return super().format(record)

LOGFILE = os.path.join(exe_dir, "mvccalc.log")

formatter = LowercaseFormatter(
    fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler = logging.FileHandler(LOGFILE, mode="w", encoding="utf-8")
handler.setFormatter(formatter)

# level=logging.DEBUG means that Matplotlib’s font manager then prints all of its font scoring attempts as debug messages when it tries to resolve your rcParams["font.family"].  That’s why it happens only the first time you run main.py after opening Spyder.
# logging.basicConfig(level=logging.DEBUG, handlers=[handler])
# THE SOLUTION IS TO CHANGE DEBUG -> INFO
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

# logging.basicConfig(
#     level=logging.DEBUG,
#     filename=LOGFILE,
#     filemode="w",       # overwrite each run
#     encoding="utf-8",
#     format="[{asctime}]:{levelname}:{message}",
#     style="{",
#     datefmt="%Y-%m-%d %H:%M:%S",
# )

# Enable faulthandler to dump tracebacks on segfaults
# faulthandler.enable(file=open(LOGFILE, "a"))

# with open(LOGFILE, "a") as fh:
#     faulthandler.enable(file=fh)

faulthandler_log = open(LOGFILE, "a")
faulthandler.enable(file=faulthandler_log)


def _log_uncaught_exceptions(exctype, value, tb):
    logging.critical("Uncaught exception", exc_info=(exctype, value, tb))


sys.excepthook = _log_uncaught_exceptions



def main():
    QtWidgets.QApplication.setAttribute(
        QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QtWidgets.QApplication(sys.argv)

    pixmap = QPixmap(base_path('resources/icons', 'bmc_logo_splash.png'))
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

    update_splash(splash, "CONNECTING TO DATABASE", 60)
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
            
            self.logger = SBConsoleOutput(
                target=self.ledt_output,
                formatter=formatter,
                send_button=self.btn_sendLog,  
                logfile=LOGFILE                 
            )

            logging.info("=== Session started ===")
            
    
            QtCore.QTimer.singleShot(0, lambda: self.ledt_output.verticalScrollBar().setValue(self.ledt_output.verticalScrollBar().maximum()))
                    
            # # Force initial scroll to bottom
            # sb = self.ledt_output.verticalScrollBar()
            # if sb is not None:
            #     sb.setValue(sb.maximum())

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
            self.plot_controller.bind_ui_controls()
            
            
            self.myFigTop = self.plot_controller.canvas 
    
            self.activateWindow()
            
            print(f"VERSIONNUMBER = {VERSIONNUMBER}")
            print(f"BUILDNUMBER   = {BUILDNUMBER}")
            print(f"GITREVHEAD    = {GITREVHEAD}")
            print(f"VERSIONNAME   = {VERSIONNAME}")
            print(f"GITTAG        = {GITTAG}")
            print(f"CONDAENVIRONMENTNAME = {CONDAENVIRONMENTNAME}")
            print(f"PYTHONVERSION = {PYTHONVERSION}")
            print(f"CONDAENVIRONMENTFILENAME = {CONDAENVIRONMENTFILENAME or '(not found)'}")
            
            self.threadpool = QThreadPool()
            print('Multithreading with maximum %d threads' %
                  self.threadpool.maxThreadCount())
            
            def log_exceptions(exctype, value, tb):
                logging.critical("Uncaught exception",
                                 exc_info=(exctype, value, tb))
            
            sys.excepthook = log_exceptions
            
            logging.info(f"=== {FRIENDLYVERSIONNAME} executable started ===")
            logging.info(f"VERSIONNUMBER = {VERSIONNUMBER}")
            logging.info(f"BUILDNUMBER   = {BUILDNUMBER}")
            logging.info(f"GITREVHEAD    = {GITREVHEAD}")
            logging.info(f"VERSIONNAME   = {VERSIONNAME}")
            logging.info(f"GITTAG        = {GITTAG}")
            logging.info(f"CONDAENVIRONMENTNAME = {CONDAENVIRONMENTNAME}")
            logging.info(f"PYTHONVERSION = {PYTHONVERSION}")
            logging.info(f"CONDAENVIRONMENTFILENAME = {CONDAENVIRONMENTFILENAME or '(not found)'}")
            logging.info("Multithreading with maximum %d threads" %
                         self.threadpool.maxThreadCount())

            self.setWindowFlag(Qt.WindowMaximizeButtonHint)
            self.setWindowFlag(Qt.WindowMinimizeButtonHint)
            self.setWindowTitle(FRIENDLYVERSIONNAME)
            self.setWindowIcon(
                QIcon(base_path('resources/icons', 'icn_b.png')))

            # self.showMaximized()

            # self.prefs = Preferences()  
            # self.load_preferences()


            self.btn_loadMat.clicked.connect(self.load_mat_files) 
            self.btn_process.clicked.connect(self.load_mat_files) 
            self.btn_export.clicked.connect(self.export_logfile) 
            self.btn_exit.clicked.connect(self.close) 
            
            self.btn_burstDetection.clicked.connect(self.on_burst_detection)


            self.file_path = None
                
            self.tw_plotting.setStyleSheet("""
                QTabBar::tab {
                    font-size: 13px;
                    padding: 8px 16px;
                    height: 15px;
                }
            """)
            self.tw_plotting.clear()
            
            # in ApplicationWindow.__init__ after self.tw_plotting is created
            self._style_tabs_for_plotting()



            # try:
            #     with h5py.File("./data/P05_MVC_Left_EXT_CAR_RAD.mat", "r") as f:
            #         print("File loader: h5py")
            # except OSError:
            #     mat = scipy.io.loadmat("./data/P05_MVC_Left_EXT_CAR_RAD.mat", struct_as_record=False, squeeze_me=True)
            #         print("File loader: scipy.io.loadmat")
                
                
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
        
            
        import xml.etree.ElementTree as ET
        from datetime import datetime
        from PyQt5.QtWidgets import QFileDialog
        import logging
        
        def export_logfile(self):
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
                payload = plot_ctrl.get_export_payload_active_row(file_label, require_three=False)
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

        
        
        # def export_logfile(self):
        #     savepath, _ = QFileDialog.getSaveFileName(
        #         self,
        #         "Export XML",
        #         "",
        #         "XML Files (*.xml)"
        #     )
        #     if not savepath:
        #         logging.info("Export cancelled: no file path selected.")
        #         return
        
        #     # Dummy session data
        #     session_data = [
        #         {
        #             "filename": "P05_MVC_Left_EXT_CAR_RAD.mat",
        #             "row": 0,
        #             "mvc": 1.234,
        #             "bursts": [(120, 240), (400, 560), (800, 950)]
        #         },
        #         {
        #             "filename": "P05_MVC_Left_ABD.mat",
        #             "row": 1,
        #             "mvc": 0.876,
        #             "bursts": [(100, 220), (500, 670), (850, 1000)]
        #         }
        #     ]
        
        #     # Build XML root
        #     root = ET.Element("MVCResults")
        
        #     # Add export timestamp
        #     now = datetime.now()
        #     export_info = ET.SubElement(root, "ExportInfo")
        #     ET.SubElement(export_info, "Date").text = now.strftime("%Y-%m-%d")
        #     ET.SubElement(export_info, "Time").text = now.strftime("%H:%M:%S")
        
        #     # Add file entries
        #     for filedata in session_data:
        #         file_el = ET.SubElement(root, "File", name=filedata["filename"])
        #         ET.SubElement(file_el, "Row").text = str(filedata["row"])
        #         ET.SubElement(file_el, "MVC").text = str(filedata["mvc"])
        
        #         bursts_el = ET.SubElement(file_el, "Bursts")
        #         for idx, (start, end) in enumerate(filedata["bursts"], 1):
        #             burst_el = ET.SubElement(bursts_el, "Burst", id=str(idx))
        #             ET.SubElement(burst_el, "Start").text = str(start)
        #             ET.SubElement(burst_el, "End").text = str(end)
        
        #         logging.info(
        #             f"Prepared export for file={filedata['filename']} row={filedata['row']} "
        #             f"MVC={filedata['mvc']} bursts={len(filedata['bursts'])}"
        #         )
        
        #     # Write XML file
        #     try:
        #         tree = ET.ElementTree(root)
        #         tree.write(savepath, encoding="utf-8", xml_declaration=True)
        
        #         directory = os.path.dirname(savepath)
        #         logging.info(f"XML export completed successfully: {savepath}")
        #         logging.info(f"Export directory: {directory}")
        #         logging.info(f"Export timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        #     except Exception as e:
        #         logging.error(f"Failed to write XML export: {e}")


        # def export_logfile(self):
        #     savepath, _ = QFileDialog.getSaveFileName(
        #         self,
        #         "Export txt",
        #         "",
        #         "Text Files (*.txt)"
        #     )
        #     if savepath:
        #         try:
        #             # Example: simulate exporting a file
        #             exported_file = "results.csv"
        
        #             # Log info about the export
        #             logging.info(f"Exporting file '{exported_file}' to '{savepath}'")
        
        #             # Actually write a minimal export file (optional)
        #             with open(savepath, "w", encoding="utf-8") as f:
        #                 f.write("MVC Calculator Export Test\n")
        #                 f.write("This is just a test line.\n")
        #                 f.write("More lines can go here...\n")
        
        #             # Confirm completion in the log
        #             logging.info(f"Export completed successfully. File saved at '{savepath}'")
        
        #         except Exception as e:
        #             logging.error(f"Export failed: {e}", exc_info=True)
        
        
        def exportXML_file(self):
            print("exportXML_file")
           
        def importXML_file(self):
            print('importXML_file')
            # dialog.matsImported.connect(self.on_mats_imported)
            # dialog.exec_()
       
        def load_mat_files(self):
            dialog = LoadMat(self)
            dialog.matsImported.connect(self.on_mats_imported)
            dialog.exec_()
            
            
        def on_burst_detection(self):
            # find current tab & its PlotController
            idx = self.tw_plotting.currentIndex()
            if idx < 0:
                QMessageBox.information(self, "Burst detection", "No plotting tab is selected.")
                return
        
            tab = self.tw_plotting.widget(idx)
            plot_ctrl = getattr(tab, "plot_ctrl", None)
            if plot_ctrl is None:
                QMessageBox.warning(self, "Burst detection", "No plot controller on this tab.")
                return
        
            # choose your sampling rate
            # If you have a global/constant, use that; otherwise set an appropriate default for sEMG.
            fs = globals().get("DEFAULT_SEMG_FREQUENCY", 2000)  # Hz fallback
        
            # run detection on the ACTIVE row (the one with bold border)
            # this will compute energy mask → intervals → paint up to 3 spans
            try:
                plot_ctrl.detect_bursts_with_energy(fs=fs, min_silence=0.080, min_sound=0.200)
            except Exception as e:
                QMessageBox.critical(self, "Burst detection error", str(e))

          
            
        def on_mats_imported(self, results):
            self.tw_plotting.clear()
            for res in results:
                base_name = os.path.basename(res["path"])
        
                tab = QWidget()
                layout = QVBoxLayout(tab)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)
                tab.setLayout(layout)
        
                # Let PlotController handle adding toolbar+canvas to the container's layout
                plot_ctrl = PlotController(parent=self, container=tab, main_window=self)
        
                # Plot in-memory arrays
                # plot_ctrl.plot_mat_arrays(res["data"], res["labels"]) ORIGINASL
                plot_ctrl.plot_mat_arrays(res["data"], res["labels"], source_path=res["path"])

          
                # Keep a reference for export
                tab.plot_ctrl = plot_ctrl
        
                self.tw_plotting.addTab(tab, base_name)

            
        # def on_mats_imported(self, results):
        #     """Called after LoadMat dialog emits imported MAT files"""
        #     self.tw_plotting.clear()
        
        #     for res in results:
        #         base_name = os.path.basename(res["path"])
        
        #         # Create new tab
        #         tab = QWidget()
        #         layout = QVBoxLayout(tab)
        #         layout.setContentsMargins(0, 0, 0, 0)  # remove padding so plots fill tab
        #         layout.setSpacing(2)
        
        #         # Attach a PlotController for this file
        #         plot_ctrl = PlotController(parent=self, container=tab, main_window=self)
        #         # layout.addWidget(plot_ctrl.toolbar)
        #         # layout.addWidget(plot_ctrl.canvas)
        
        #         # Ensure layout is set on tab
        #         tab.setLayout(layout)
        
        #         # Plot using arrays already in memory
        #         plot_ctrl.plot_mat_arrays(res["data"], res["labels"])
        
        #         # Add tab to tw_plotting
        #         self.tw_plotting.addTab(tab, base_name)
                
        #         tab.plot_ctrl = plot_ctrl

        # def on_mats_imported(self, results):
        #     self.tw_plotting.clear()
        #     for res in results:
        #         base_name = os.path.basename(res["path"])
        #         tab = QWidget()
        #         layout = QVBoxLayout(tab)
        
        #         plot_ctrl = PlotController(parent=self, container=tab, main_window=self)
        #         layout.addWidget(plot_ctrl.toolbar)
        #         layout.addWidget(plot_ctrl.canvas)
        
        #         # use in-memory arrays
        #         plot_ctrl.plot_mat_arrays(res["data"], res["labels"])
        
        #         self.tw_plotting.addTab(tab, base_name)
           
        def on_mat_files_selected(self, files):
            self.tw_plotting.clear()
            for file_path in files:
                base_name = os.path.basename(file_path)
        
                # Create a tab
                tab = QWidget()
                layout = QVBoxLayout(tab)
        
                # Create a new PlotController for this tab
                plot_ctrl = PlotController(parent=self, container=tab, main_window=self)
                plot_ctrl.canvas.setVisible(True)
                plot_ctrl.toolbar.setVisible(True)
                layout.addWidget(plot_ctrl.toolbar)
                layout.addWidget(plot_ctrl.canvas)
        
                # Load and plot the .mat file
                plot_ctrl.plot_mat_file(file_path)
        
                self.tw_plotting.addTab(tab, base_name)            








            # for f in files:
            #     logging.info(f"Loaded MAT file: {os.path.basename(f)}") 
            #     # --- Update plotting tabs ---
            #     self.tw_plotting.clear()
            #     for file_path in files:
            #         base_name = os.path.basename(file_path)
            #         tab = QWidget()
            #         layout = QVBoxLayout(tab)
            #         # Example: put a QLabel or custom plotting widget inside
            #         label = QLabel(base_name)   # <<== show actual file name, not literal string
            #         layout.addWidget(label)
                    
            #         self.tw_plotting.addTab(tab, base_name)






                    
        # def export_logfile(self):
        #     savepath, _ = QFileDialog.getSaveFileName(
        #         self,
        #         "Export txt",
        #         "",
        #         "Text Files (*.txt)"
        #     )
        #     if savepath:
        #         with open(savepath, "w") as f:
        #             f.write("MVC Calculator Export Test\n")
        #             f.write("This is just a test line.\n")
        #             f.write("More lines can go here...\n")
                    
            # if savepath:
            #     with open(savepath, "w") as f:
            #         f.write("MVC Calculator Results\n")
            #         f.write("=======================\n\n")
            #         for key, value in self.results.items():
            #             f.write(f"{key}: {value}\n")

            
        # def load_mat_files(self):
        #     dialog = LoadMat(self)
        #     if dialog.exec_() == QDialog.Accepted:
        #         files = dialog.get_selected_files()
        #         if files:
        #             current = self.ledt_output.toPlainText()
        #             names = "\n".join(os.path.basename(f) for f in files)
        #             new_text = current + "\n" + names if current else names
        #             self.ledt_output.setPlainText(new_text)
        #             if isinstance(self.ledt_output, QPlainTextEdit):
        #                 self.ledt_output.setPlainText(names)
        #             else:
        #                 # fallback if it's still a QLineEdit
        #                 self.ledt_output.setText(" ; ".join(os.path.basename(f) for f in files))
            
        #     self.tw_plotting.clear()

        #     for file_path in files:
        #         base_name = os.path.basename(file_path)
        
        #         # Create a QWidget for this tab
        #         tab = QWidget()
        #         layout = QVBoxLayout(tab)
        
        #         # Example: put a QLabel or custom plotting widget inside
        #         label = QLabel(f"base_name")
        #         layout.addWidget(label)
        
        #         # Add to QTabWidget
        #         self.tw_plotting.addTab(tab, base_name)
    
        # def load_mat_files(self):
        #     dialog = LoadMat(self)
        #     if dialog.exec_() == QDialog.Accepted:
        #         files = dialog.get_selected_files()
        #         if files:
        #             self.ledt_output.setText("\n".join(os.path.basename(f) for f in files))

        # # main.py — wherever you open the dialog
        # def load_preferences(self):
        #     dialog = PreferencesDialog(self)
        #     dialog.setWindowTitle("Preferencias")
        #     result = dialog.exec_()
        #     if result == QtWidgets.QDialog.Accepted:
        #         # If your dialog writes into self.prefs, persist to disk:
        #         self.prefs.save()
        #         # Re-apply visibility
        #         hide = self.prefs.get(
        #             "General", "hide_experimental", fallback="True") == "True"
        #         self.apply_experimental_visibility(hide)

         


        # def one_button_click(self):
        #     dialog = InputDialogONECLICK(self)
        #     dialog.exec_()

        # def open_imu_positioning_dialog(self):
        #     self.dialog = ImuPositioningDialog(self)
        #     self.dialog.show()

        # def save_csv(self, savepath):
        #     try:
        #         # savepath = QFileDialog.getSaveFileName(self, "Guardar csv","","*.csv")[0]
        #         self.imported_MOT.to_csv(savepath, sep=',')
        #     except:
        #         pass

  
        # def show_ik_dialog(self):
        #     self.dialog = IkDialog(self)
        #     self.dialog.show()  # or dialog.show() for non-blocking

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


        # def closeEvent(self, event):
        #     print("[INFO] Window is closing...")
        
        #     # 1) Stop UI timers
        #     try:
        #         if hasattr(self, "update_timer") and self.update_timer:
        #             self.update_timer.stop()
        #     except Exception:
        #         pass
        
        #     # 2) Stop recording if active
        #     try:
        #         if getattr(self, "is_recording", False) and hasattr(self, "camera") and self.camera:
        #             self.camera.stop_recording()
        #             self.is_recording = False
        #     except Exception:
        #         pass
        
        #     # 3) Stop the camera
        #     try:
        #         if hasattr(self, "camera") and self.camera:
        #             self.camera.stop()
        #     except Exception:
        #         pass
        #     finally:
        #         self.camera = None
        
        #     # 4) Remove & delete the viewfinder widget so it doesn't linger in the layout
        #     try:
        #         if hasattr(self, "_current_viewfinder") and self._current_viewfinder:
        #             # Remove from its parent layout if we can
        #             try:
        #                 if hasattr(self, "labelWebcamFeed") and self.labelWebcamFeed and self.labelWebcamFeed.parentWidget():
        #                     parent_layout = self.labelWebcamFeed.parentWidget().layout()
        #                     if parent_layout:
        #                         parent_layout.removeWidget(self._current_viewfinder)
        #             except Exception:
        #                 pass
        #             self._current_viewfinder.hide()
        #             self._current_viewfinder.deleteLater()
        #     except Exception:
        #         pass
        #     finally:
        #         self._current_viewfinder = None
        
        #     # 5) Restore the placeholder label (nice-to-have)
        #     try:
        #         if hasattr(self, "labelWebcamFeed") and self.labelWebcamFeed:
        #             self.labelWebcamFeed.show()
        #             self.labelWebcamFeed.setText("Cámara desactivada.")
        #     except Exception:
        #         pass
        
        #     # 6) App-specific cleanup (Bluetooth, video device handles, logs, etc.)
        #     try:
        #         self.cleanUp()
        #     except Exception as e:
        #         print("Error during app cleanup:", e)
        #         logging.critical("Critical error during cleanUp()", exc_info=True)
        
        #     # 7) Hand off to Qt
        #     super().closeEvent(event)


        # def closeEvent(self, event):
        #     print("[INFO] Window is closing...")
        #     try:
        #         if hasattr(self, "camera") and self.camera:
        #             try:
        #                 self.camera.stop()
        #             except Exception:
        #                 pass
        #             self.camera = None
        #     except Exception:
        #         pass
        
        #     try:
        #         self.cleanUp()
        #     except Exception as e:
        #         print("Error during app cleanup:", e)
        #         logging.critical("Critical error during cleanUp()", exc_info=True)
        
        #     super().closeEvent(event)


        # def closeEvent(self, event):
        #     print("[INFO] Window is closing...")

        #     if hasattr(self.camera, "image_data"):
        #         try:
        #             self.camera.image_data.disconnect(self.update_video_frame)
        #         except Exception:
        #             pass
        #         self.camera.stop()
        #         self.camera = None

            # try:
            #     if hasattr(self, "camera"):
            #         self.camera.stop()
            #         self.update_camera_toggle_button_text()
            #         logging.info("Camera stopped via closeEvent.")
            # except Exception as e:
            #     print("Error stopping camera:", e)
            #     logging.warning("Error during camera stop.", exc_info=True)

            # try:
            #     self.cleanUp()
            # except Exception as e:
            #     print("Error during app cleanup:", e)
            #     logging.critical(
            #         "Critical error during cleanUp()", exc_info=True)

            # # Proceed with normal Qt cleanup
            # super().closeEvent(event)

# %% PROGRAM CLEANUP

        def cleanUp(self):
            logging.info("Starting application cleanup...")
            logging.shutdown()

            # === Disconnect Bluetooth Socket ===
            try:
                self.socket.disconnectFromService()
                logging.info("Bluetooth disconnected.")
            except Exception as e:
                print("No Bluetooth connected. Closing...")
                logging.info(f"No Bluetooth connection to close: {e}")

            # === Close Video Device ===
            try:
                self.record_video.close_camera()
                logging.info("Video device closed.")
            except Exception as e:
                print("No video device connected. Closing...")
                logging.info(f"No video device connected to close: {e}")
            print("[INFO] Safe shutdown complete.")

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
