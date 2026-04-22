from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import scipy.io

HDF5_SIGNATURE = b"\x89HDF\r\n\x1a\n"


def is_hdf5_mat(path: str | Path) -> bool:
    """Return True when a .mat file is MATLAB v7.3 (HDF5 container)."""
    p = Path(path)
    with p.open("rb") as fh:
        return fh.read(len(HDF5_SIGNATURE)) == HDF5_SIGNATURE


def load_mat_for_mvc(path: str | Path) -> dict[str, Any]:
    """Load a MAT file and return the dict shape expected by LoadMat."""
    p = Path(path)
    if is_hdf5_mat(p):
        data, labels = _load_via_h5py(p)
    else:
        data, labels = _load_via_scipy(p)

    data = _normalize_data(data)
    labels = _normalize_labels(labels, expected_count=data.shape[0])
    return {"path": str(p), "data": data, "labels": labels}


def _load_via_scipy(path: Path) -> tuple[np.ndarray, list[str]]:
    mat = scipy.io.loadmat(path, struct_as_record=False, squeeze_me=True)
    key = next((k for k in mat.keys() if not k.startswith("__")), None)
    if not key:
        raise ValueError("MAT file has no non-metadata variables.")

    trial = mat[key]
    analog = getattr(trial, "Analog", None)
    if analog is None:
        raise ValueError("MAT file does not expose Analog structure.")

    data = getattr(analog, "Data", None)
    labels = getattr(analog, "Labels", None)
    if data is None:
        raise ValueError("MAT file Analog.Data was not found.")

    return np.asarray(data), _to_label_list(labels)


def _load_via_h5py(path: Path) -> tuple[np.ndarray, list[str]]:
    import h5py

    with h5py.File(path, "r") as h5f:
        root_name = _first_data_key(h5f)
        root_obj = _resolve_obj(h5f, h5f[root_name])
        analog_obj = _find_analog_obj(h5f, root_obj)
        if analog_obj is None:
            raise ValueError("Could not find Analog group in HDF5 MAT.")

        data_obj = _resolve_obj(h5f, _get_child_case_insensitive(analog_obj, "Data"))
        labels_obj = _resolve_obj(h5f, _get_child_case_insensitive(analog_obj, "Labels"))
        data = _dataset_to_array(h5f, data_obj)
        labels = _to_label_list(_dataset_to_labels(h5f, labels_obj))
        return data, labels


def _first_data_key(h5f: Any) -> str:
    for key in h5f.keys():
        if key.startswith("__") or key == "#refs#":
            continue
        return key
    raise ValueError("HDF5 MAT file has no data keys.")


def _resolve_obj(h5f: Any, obj: Any) -> Any:
    import h5py

    if isinstance(obj, h5py.Reference):
        return h5f[obj]

    if isinstance(obj, h5py.Dataset):
        value = obj[()]
        if isinstance(value, h5py.Reference):
            return h5f[value]
        if isinstance(value, np.ndarray) and value.dtype == object and value.size == 1:
            maybe_ref = value.flat[0]
            if isinstance(maybe_ref, h5py.Reference):
                return h5f[maybe_ref]
    return obj


def _find_analog_obj(h5f: Any, root_obj: Any) -> Any | None:
    import h5py

    stack = [root_obj]
    seen_ids: set[int] = set()
    while stack:
        current = _resolve_obj(h5f, stack.pop())
        if id(current) in seen_ids:
            continue
        seen_ids.add(id(current))

        if isinstance(current, h5py.Group):
            if "Analog" in current:
                return _resolve_obj(h5f, current["Analog"])
            for key in current.keys():
                if key == "#refs#":
                    continue
                stack.append(current[key])
    return None


def _get_child_case_insensitive(group: Any, name: str) -> Any:
    for key in group.keys():
        if key.lower() == name.lower():
            return group[key]
    raise ValueError(f"Expected '{name}' under Analog in HDF5 MAT.")


def _dataset_to_array(h5f: Any, obj: Any) -> np.ndarray:
    import h5py

    resolved = _resolve_obj(h5f, obj)
    if isinstance(resolved, h5py.Dataset):
        arr = resolved[()]
    else:
        raise ValueError("Analog.Data is not a dataset in HDF5 MAT.")

    # MATLAB v7.3 can store cell arrays as object refs.
    if isinstance(arr, np.ndarray) and arr.dtype == object:
        rows = []
        for ref in arr.ravel(order="F"):
            if isinstance(ref, h5py.Reference):
                rows.append(np.asarray(h5f[ref][()]).squeeze())
        if rows:
            return np.vstack(rows)
    return np.asarray(arr)


def _dataset_to_labels(h5f: Any, obj: Any) -> Any:
    import h5py

    resolved = _resolve_obj(h5f, obj)
    if isinstance(resolved, h5py.Dataset):
        arr = resolved[()]
    else:
        raise ValueError("Analog.Labels is not a dataset in HDF5 MAT.")

    if isinstance(arr, np.ndarray) and arr.dtype == object:
        labels: list[str] = []
        for ref in arr.ravel(order="F"):
            if isinstance(ref, h5py.Reference):
                labels.append(_decode_text(np.asarray(h5f[ref][()])))
        return labels
    return arr


def _normalize_data(data: Any) -> np.ndarray:
    arr = np.asarray(data).squeeze()
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    elif arr.ndim != 2:
        raise ValueError(f"Expected 1D/2D signal matrix, got shape {arr.shape}.")
    return arr


def _normalize_labels(labels: list[str], expected_count: int) -> list[str]:
    cleaned = [str(x).strip() for x in labels if str(x).strip()]
    if not cleaned:
        cleaned = [f"EMG{i+1}" for i in range(expected_count)]

    if len(cleaned) < expected_count:
        cleaned.extend([f"EMG{i+1}" for i in range(len(cleaned), expected_count)])
    return cleaned[:expected_count]


def _to_label_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]

    arr = np.asarray(raw)
    if arr.dtype.kind == "U":
        return [str(x) for x in arr.ravel(order="F")]
    if arr.dtype.kind == "S":
        return [
            bytes(x).decode("utf-8", errors="ignore").strip()
            for x in arr.ravel(order="F")
        ]

    if arr.dtype.kind in ("i", "u") and arr.ndim >= 1:
        if arr.ndim == 2 and min(arr.shape) > 1:
            return [_decode_text(arr[:, i]) for i in range(arr.shape[1])]
        return [_decode_text(arr)]

    if arr.dtype == object:
        out: list[str] = []
        for item in arr.ravel(order="F"):
            out.append(_decode_text(item))
        return out

    return [str(raw)]


def _decode_text(value: Any) -> str:
    arr = np.asarray(value)
    if arr.size == 0:
        return ""
    if arr.dtype.kind == "U":
        return "".join(str(x) for x in arr.ravel(order="F")).strip()
    if arr.dtype.kind == "S":
        return "".join(
            bytes(x).decode("utf-8", errors="ignore")
            for x in arr.ravel(order="F")
        ).strip()

    if arr.dtype.kind in ("i", "u"):
        chars = [chr(int(x)) for x in arr.ravel(order="F") if int(x) > 0]
        return "".join(chars).strip()

    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="ignore").strip()

    return str(value).strip()
