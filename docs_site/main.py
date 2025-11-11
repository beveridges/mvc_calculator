from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

def define_env(env):
    """Expose VERSIONNAME from utilities/version_info.py"""
    version_file = Path(__file__).parent.parent / "utilities" / "version_info.py"
    if version_file.exists():
        spec = spec_from_file_location("version_info", version_file)
        v = module_from_spec(spec)
        spec.loader.exec_module(v)
        env.variables["version"] = getattr(v, "VERSIONNAME", "unknown")
    else:
        env.variables["version"] = "unknown"
