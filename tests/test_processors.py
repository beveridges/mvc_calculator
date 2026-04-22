"""Tests for processors.processors.Processor.

Processor imports PyQt5, so this module is skipped when PyQt5 is unavailable.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.requires_qt, pytest.mark.requires_numpy, pytest.mark.requires_scipy]

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


@pytest.fixture
def proc(qapp):
    from processors.processors import Processor
    return Processor(winsize=3)


class TestStaticHelpers:
    def test_bandpass_returns_same_length_array(self, proc):
        fs = 1500
        t = np.linspace(0, 1.0, fs, endpoint=False)
        x = np.sin(2 * np.pi * 100 * t)
        y = proc.bandpass(x, fs, lo=20, hi=450, order=4)
        assert y.shape == x.shape
        assert np.all(np.isfinite(y))

    def test_hampel_filter_replaces_spikes(self, proc):
        x = np.ones(101) * 10.0
        x[50] = 1e6  # obvious outlier
        y = proc.hampel_filter(x, win_samples=21, k=3.0)
        assert abs(y[50] - 10.0) < 1e-6

    def test_hampel_filter_forces_odd_window(self, proc):
        x = np.zeros(20)
        # Passing an even window should not crash - internal OR-with-1 makes it odd.
        y = proc.hampel_filter(x, win_samples=10)
        assert y.shape == x.shape

    def test_moving_rms_matches_length(self, proc):
        x = np.ones(100) * 4.0
        y = proc.moving_rms(x, win_samples=10)
        assert y.shape == x.shape
        assert np.all(np.isfinite(y))
        # RMS of all-fours should be ~4 in the interior.
        assert abs(y[50] - 4.0) < 1e-6


class TestCleanSemg:
    def test_returns_empty_for_all_nan(self, proc):
        x = np.array([np.nan] * 100)
        out = proc.clean_semg(x, fs=1500)
        assert out.size == 0

    def test_returns_positive_envelope(self, proc):
        rng = np.random.default_rng(0)
        x = rng.normal(0, 1.0, size=3000)
        out = proc.clean_semg(x, fs=1500, rms_ms=50, hampel_ms=50)
        assert out.shape == x.shape
        assert np.all(out >= 0)
        assert np.all(np.isfinite(out))


class TestEnergyDetection:
    def test_rejects_when_min_sound_not_larger(self, proc):
        x = np.zeros(1000)
        with pytest.raises(ValueError):
            proc.energy_detection(x, min_silence=0.2, min_sound=0.1, fs=100)

    def test_handles_empty_input(self, proc):
        x = np.array([], dtype=float)
        ev, out = proc.energy_detection(x, fs=1000)
        assert ev.size == 0
        assert out.size == 0

    def test_detects_three_bursts_and_ignores_extra(self, proc):
        fs = 1000
        x = np.zeros(fs * 5)
        # Create 5 bursts, each 250 ms = 250 samples
        burst_len = 250
        for start_s in [0.3, 1.0, 2.0, 3.0, 4.0]:
            s = int(start_s * fs)
            x[s : s + burst_len] = 1.0
        ev, out = proc.energy_detection(x, min_silence=0.08, min_sound=0.20, fs=fs)
        # At most 3 bursts kept, same length, mask is binary
        assert ev.shape == x.shape
        assert set(np.unique(ev).tolist()).issubset({0, 1})
        # Output is zeroed where mask is zero
        assert np.all(out[ev == 0] == 0)
        # Number of distinct bursts in mask <= 3
        diffs = np.diff(np.concatenate(([0], ev, [0])))
        n_bursts = int(((diffs == 1).sum()))
        assert n_bursts <= 3


class TestMVCMatlab:
    def test_returns_nan_for_empty_input(self, proc):
        mvc, rms = proc.mvc_matlab(np.array([np.nan, np.nan]))
        assert np.isnan(mvc)
        assert rms.size == 0

    def test_short_signal_falls_back_without_filter(self, proc):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mvc, rms = proc.mvc_matlab(x)
        assert np.isfinite(mvc)
        assert rms.shape == x.shape

    def test_large_signal_returns_max_envelope(self, proc):
        rng = np.random.default_rng(1)
        x = rng.normal(0, 2.0, size=2000)
        mvc, rms = proc.mvc_matlab(x)
        assert np.isfinite(mvc)
        assert rms.shape == x.shape
        assert mvc == pytest.approx(np.nanmax(rms))

    def test_mvc_rejects_high_cutoff_above_nyquist(self, monkeypatch, proc):
        # Temporarily replace the default frequency with something that makes
        # fcuthigh (500 Hz) violate the Nyquist check.
        from processors import processors as p_mod
        monkeypatch.setattr(p_mod, "DEFAULT_SEMG_FREQUENCY", 600)
        with pytest.raises(ValueError):
            proc.mvc_matlab(np.ones(5000))


class TestMovingRmsMatlab:
    def test_zeros_return_zeros(self, proc):
        x = np.zeros(50)
        y = proc.moving_rms_matlab(x, halfwindow=5)
        assert np.allclose(y, 0.0)

    def test_constant_values_return_constant(self, proc):
        x = np.ones(50) * 3.0
        y = proc.moving_rms_matlab(x, halfwindow=5)
        assert np.allclose(y, 3.0)
