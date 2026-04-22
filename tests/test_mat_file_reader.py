from __future__ import annotations

import numpy as np
import scipy.io
import h5py

from utilities.mat_file_reader import is_hdf5_mat, load_mat_for_mvc


def test_load_classic_mat_via_scipy(tmp_path):
    path = tmp_path / "classic.mat"

    analog = np.empty((1, 1), dtype=[("Data", "O"), ("Labels", "O")])
    analog["Data"][0, 0] = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    analog["Labels"][0, 0] = np.array(["EMG1", "EMG2"], dtype=object)
    trial = np.empty((1, 1), dtype=[("Analog", "O")])
    trial["Analog"][0, 0] = analog
    scipy.io.savemat(path, {"Trial": trial})

    out = load_mat_for_mvc(path)
    assert out["path"].endswith("classic.mat")
    assert out["data"].shape == (2, 3)
    assert out["labels"] == ["EMG1", "EMG2"]
    assert is_hdf5_mat(path) is False


def test_load_hdf5_mat_via_h5py(tmp_path):
    path = tmp_path / "v73.mat"
    with h5py.File(path, "w") as h5f:
        trial = h5f.create_group("Trial")
        analog = trial.create_group("Analog")
        analog.create_dataset("Data", data=np.array([[10.0, 20.0], [30.0, 40.0]]))
        analog.create_dataset("Labels", data=np.array([b"TA", b"MG"]))

    out = load_mat_for_mvc(path)
    assert out["data"].shape == (2, 2)
    assert out["labels"] == ["TA", "MG"]
    assert is_hdf5_mat(path) is True


def test_labels_are_padded_to_match_data_rows(tmp_path):
    path = tmp_path / "labels_short.mat"
    with h5py.File(path, "w") as h5f:
        trial = h5f.create_group("Trial")
        analog = trial.create_group("Analog")
        analog.create_dataset("Data", data=np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
        analog.create_dataset("Labels", data=np.array([b"OnlyOne"]))

    out = load_mat_for_mvc(path)
    assert out["data"].shape == (3, 3)
    assert out["labels"] == ["OnlyOne", "EMG2", "EMG3"]
