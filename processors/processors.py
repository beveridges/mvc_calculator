# /processors/processors.py

import math
import numpy as np
import os
import pandas as pd
from scipy.signal import butter, filtfilt


# -- PYQT -----------------------
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QIcon

# -- CUSTOM ---------------------
from config.defaults import DEFAULT_SEMG_FREQUENCY
from utilities.path_utils import resource_path
from utilities.path_utils import base_path

WINSIZE = 3

class Processor:
    def __init__(self, winsize=3):
        self.winsize = winsize

    def boop(self):
        return "BOOP!"

    def moving_rms(self, interval, halfwindow):
        n = len(interval)
        rms_signal = np.zeros(n)
        for i in range(n):
            small_index = max(0, i - halfwindow)
            big_index   = min(n, i + halfwindow)
            window_samples = interval[small_index:big_index]
            rms_signal[i] = np.sqrt(np.sum(window_samples**2)/len(window_samples))
        return rms_signal

    def mvc(self, in_vec):
        in_vec = in_vec[~np.isnan(in_vec)]
        in_vec = in_vec - np.mean(in_vec)

        signal_corrected = in_vec.copy()
        signal_corrected[signal_corrected > 9800] = 0

        # Bandpass filter
        fcutlow, fcuthigh = 50, 500
        b, a = butter(4, [fcutlow, fcuthigh], btype="band", fs=DEFAULT_SEMG_FREQUENCY)
        signal_bp = filtfilt(b, a, signal_corrected)

        full_wave_rectified = np.abs(signal_bp)

        movingrms = self.moving_rms(full_wave_rectified, self.winsize)

        MVC = np.nanmax(movingrms)
        return MVC, movingrms
