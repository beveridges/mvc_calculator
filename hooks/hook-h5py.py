# PyInstaller hook for h5py (MATLAB v7.3 / HDF5 .mat via scipy.io.loadmat)
# SciPy imports h5py only when reading HDF5-based MAT files; PyInstaller will not
# trace it from the dependency graph without explicit collection.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

datas = []
binaries = []
hiddenimports = []

try:
    from PyInstaller.utils.hooks import collect_all

    _d, _b, _h = collect_all("h5py")
    datas += _d
    binaries += _b
    hiddenimports += _h
except ImportError:
    pass

try:
    hiddenimports += collect_submodules("h5py")
except Exception:
    pass

try:
    datas += collect_data_files("h5py")
except Exception:
    pass

try:
    binaries += collect_dynamic_libs("h5py")
except Exception:
    pass

hiddenimports += [
    "h5py",
    "h5py._errors",
    "h5py._hl",
]
