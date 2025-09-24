# /dialogs/load_mat_dialog.py
import h5py # load mat
import math
import numpy as np
import os
import pandas as pd
import scipy.io # load mat

# -- PYQT -----------------------
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

# -- CUSTOM ---------------------
# from processors.processors import mvc
from utilities.path_utils import resource_path
from utilities.path_utils import base_path


class LoadMat(QDialog):
    filesSelected = pyqtSignal(list)
    def __init__(self, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(base_path("uis", "loadMat.ui"))
        uic.loadUi(ui_path, self)
        self.setWindowIcon(QIcon(resource_path('icons', 'icn_matlab.png')))

        self.paths = []
        self.minRows = None
        self.minRecordingLengthSecs = None
        
        # Connect buttons
        self.btnSelectFiles.clicked.connect(lambda: self.select_files("*.mat"))
        self.btnClose.clicked.connect(self.close_dialog)

    # getter
    def get_selected_files(self, filter_mask="*.mat"):        
        paths, _ = QFileDialog.getOpenFileNames(self, "Select MAT files", "", f"MAT files ({filter_mask})")
        if paths:
            self.paths = paths   # ✅ store them
            self.filesSelected.emit(paths)  # ✅ emit directly


    def select_files(self, file_extension):
        preferred_dirs = [os.path.join(base_path("data"))]

        for path in preferred_dirs:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Open", path, file_extension)
            if files:
                self.paths = files
                self.listFiles.clear()
                for path in self.paths:
                    item = QListWidgetItem(path)
                    item.setToolTip(path)  # Show full path on hover
                    self.listFiles.addItem(item)
                self.filesSelected.emit(self.paths)
                return  # done — don't fall through to next folder
            elif files == []:
                return  # user canceled — don't open another dialog

        print("No files selected.")


    def close_dialog(self):
        self.accept()
        self.close()

