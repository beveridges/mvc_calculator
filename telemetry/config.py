# telemetry/config.py

import sys
import os

# Detect PyInstaller frozen mode
RUNNING_FROZEN = getattr(sys, "frozen", False)

# Default behavior:
#   • Only enable telemetry when running a frozen (PyInstaller) build
#   • Disable telemetry when running normal Python source
ENABLE_TELEMETRY = RUNNING_FROZEN

# Allow override via environment variable:
#   TELEMETRY=0      → force disable
#   TELEMETRY=1      → force enable
#   TELEMETRY=false  → disable
#   TELEMETRY=true   → enable
if "TELEMETRY" in os.environ:
    ENABLE_TELEMETRY = os.environ["TELEMETRY"].lower() not in ("0", "false")

# Performance sampling interval (heartbeat)
PERF_SAMPLE_INTERVAL = 60  # seconds
