# PyInstaller hook for scipy
# This hook ensures all scipy modules and binaries are collected

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# Initialize collections
datas = []
binaries = []
hiddenimports = []

# Try to use collect_all if available (PyInstaller 4.0+)
try:
    from PyInstaller.utils.hooks import collect_all
    datas, binaries, hiddenimports = collect_all('scipy')
except ImportError:
    # Fallback for older PyInstaller versions
    pass

# Collect submodules explicitly
try:
    hiddenimports += collect_submodules('scipy')
except Exception:
    pass

# Collect data files
try:
    datas += collect_data_files('scipy')
except Exception:
    pass

# Collect dynamic libraries (DLLs on Windows, .so on Linux)
try:
    binaries += collect_dynamic_libs('scipy')
except Exception:
    pass

# Explicitly add scipy.io and related modules (critical for .mat file import)
hiddenimports += [
    'scipy',
    'scipy.io',
    'scipy.io.matlab',
    'scipy.io.matlab.mio',
    'scipy.io.matlab.mio5',
    'scipy.io.matlab.mio5_params',
    'scipy.io.matlab.mio5_utils',
    'scipy.signal',
    'scipy.sparse',
    'scipy.spatial',
    'scipy.stats',
    'scipy._lib',
    'scipy._lib._ccallback',
]

