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


class Processor:
    
    def __init__(self, winsize=3):
        self.winsize = winsize
        
    @staticmethod  
    def bandpass(x, fs, lo=20, hi=450, order=4):
        b, a = butter(order, [lo, hi], btype="band", fs=fs)
        return filtfilt(b, a, x)
    
    
    @staticmethod
    def hampel_filter(x, win_samples=51, k=3.0):
        x = np.asarray(x, float); n = x.size
        w = int(win_samples) | 1; half = w // 2
        y = x.copy()
        for i in range(n):
            lo = max(0, i - half); hi = min(n, i + half + 1)
            seg = x[lo:hi]; med = np.median(seg)
            mad = np.median(np.abs(seg - med)) + 1e-12
            if abs(x[i] - med) > k * 1.4826 * mad:
                y[i] = med
        return y
    
    @staticmethod
    def moving_rms(x, win_samples):
        # centered window via convolution
        w = np.ones(win_samples) / win_samples
        return np.sqrt(np.convolve(x**2, w, mode="same"))


    def clean_semg(self, x, fs, rms_ms=50, hampel_ms=50):
        x = np.asarray(x, float)
        x = x[~np.isnan(x)]
        if x.size == 0:
            return x

        x = type(self).bandpass(x, fs, lo=50, hi=500)
        x = np.abs(x) 
        rms = type(self).moving_rms(x, max(1, int(fs * rms_ms / 1000)))
        rms_h = type(self).hampel_filter(rms, max(3, int(fs * hampel_ms / 1000)) | 1, k=3.0)
        return rms_h

    def energy_detection(self, in_audio: np.ndarray,
                         min_silence: float = 0.080,
                         min_sound: float = 0.200,
                         fs: int = 44100):
        """
        Time-domain energy detection (NumPy port of your MATLAB code).
    
        Parameters
        ----------
        in_audio : np.ndarray 1-D signal.
        min_silence : float Minimum silence length in seconds. Default 0.080.
        min_sound : float Minimum sound length in seconds. Default 0.200.
        fs : int Sampling frequency. Default 44100.
    
        Returns
        -------
        energy_vector : np.ndarray 0/1 mask (same length as input) where 1 marks detected sound.
        out_audio : np.ndarray in_audio multiplied by energy_vector (silence is zeroed).
        """
        x = np.asarray(in_audio).astype(float).ravel()
    
        if min_sound <= min_silence:
            raise ValueError("min_sound must be larger than min_silence")
    
        # --- Initial variables
        energy = np.abs(x) ** 2
        energy_vector = np.ones(len(x), dtype=int)
    
        min_silence_samples = max(1, int(round(min_silence * fs)))
        min_sound_samples   = max(1, int(round(min_sound * fs)))
    
        # --- Moving average filter over 'min_silence' window (like filter(b,a,...))
        L = min_silence_samples
        b = np.ones(L, dtype=float) / L
        # same-length output (centered like MATLAB filter on long signals)
        moving_ave = np.convolve(energy, b, mode="same")
        max_ma = moving_ave.max() if moving_ave.size else 1.0
        if max_ma > 0:
            moving_ave = moving_ave / max_ma
    
        # --- Silence detection threshold
        energy_vector[moving_ave < 0.010] = 0
    
        # --- Enforce minimum sound length (remove short 1-runs)
        cum = 0
        for i in range(len(energy_vector)):
            if energy_vector[i]:
                cum += 1
            else:
                if 0 < cum < min_sound_samples:
                    energy_vector[i - cum:i] = 0
                cum = 0
        # Handle a trailing run of ones
        if 0 < cum < min_sound_samples:
            energy_vector[len(energy_vector) - cum:len(energy_vector)] = 0
    
        out_audio = x * energy_vector
        return energy_vector, out_audio

    def moving_rms_matlab(self, interval, halfwindow):
        n = len(interval)
        rms_signal = np.zeros(n)
        for i in range(n):
            small_index = max(0, i - halfwindow)
            big_index   = min(n, i + halfwindow)
            window_samples = interval[small_index:big_index]
            rms_signal[i] = np.sqrt(np.sum(window_samples**2)/len(window_samples))
        return rms_signal


    def mvc_matlab(self, in_vec):
        x = np.asarray(in_vec, dtype=float)
        x = x[~np.isnan(x)]
        if x.size == 0:
            return np.nan, x  # nothing to do
    
        x = x - np.mean(x)
    
        # Zero out obvious spikes
        signal_corrected = x.copy()
        signal_corrected[signal_corrected > 9800] = 0.0
    
        # Bandpass filter
        fcutlow, fcuthigh = 50.0, 500.0
        if fcuthigh >= 0.5 * DEFAULT_SEMG_FREQUENCY:
            raise ValueError("fcuthigh must be < Nyquist")
        b, a = butter(
            N=4,
            Wn=[fcutlow, fcuthigh],
            btype="band",
            fs=DEFAULT_SEMG_FREQUENCY
        )
    
        # Ensure length is sufficient for filtfilt
        padlen = 3 * max(len(a), len(b))
        if signal_corrected.size <= padlen:
            # fall back to no filter or a simpler approach
            signal_bp = signal_corrected
        else:
            signal_bp = filtfilt(b, a, signal_corrected)
    
        # Rectify + RMS envelope
        full_wave_rectified = np.abs(signal_bp)
        movingrms = self.moving_rms_matlab(full_wave_rectified, self.winsize)
    
        MVC = np.nanmax(movingrms) if movingrms.size else np.nan
        return MVC, movingrms
    