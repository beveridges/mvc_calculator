#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service wrapper for auto-license email handler.

This script provides a clean interface for running the email handler as a service/daemon.
It handles graceful shutdown and can be used with systemd (Linux) or Task Scheduler (Windows).

Usage:
    python run_auto_license_service.py

For Windows Task Scheduler:
    - Create a task that runs this script
    - Set it to run at startup or on a schedule
    - Use "pythonw.exe" to run without console window

For Linux systemd:
    - Create a service file in /etc/systemd/system/
    - Example service file content:
      [Unit]
      Description=MVC Calculator Auto-License Email Handler
      After=network.target

      [Service]
      Type=simple
      User=your_user
      WorkingDirectory=/path/to/MVC_CALCULATOR/scripts
      ExecStart=/usr/bin/python3 /path/to/MVC_CALCULATOR/scripts/run_auto_license_service.py
      Restart=always
      RestartSec=10

      [Install]
      WantedBy=multi-user.target
"""

import signal
import sys
import logging
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auto_license_email_handler import main_loop

# Setup basic logging for service wrapper
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_requested = True
    # The main_loop will check for KeyboardInterrupt, so we can raise it
    raise KeyboardInterrupt


def main():
    """Main entry point for service."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # On Windows, also handle SIGBREAK
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, signal_handler)
        except AttributeError:
            # SIGBREAK might not be available on all Windows versions
            pass
    
    logger.info("Starting MVC Calculator Auto-License Email Handler Service")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service crashed with error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Service shutdown complete")


if __name__ == "__main__":
    main()

