#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service wrapper for the AI Mail Responder.

Run the responder as a long-lived process. Graceful shutdown is handled inside
ai_mail_responder (SIGINT/SIGTERM). Use this script when running under
systemd (Linux) or Task Scheduler (Windows).

Usage:
    python run_ai_responder_service.py

Environment variables (see AI_MAIL_RESPONDER_README.md):
    AI_RESPONDER_MAILBOX_PASS, AI_RESPONDER_OPENAI_API_KEY,
    AI_RESPONDER_UNIVERSAL_LICENSE_KEY or AI_RESPONDER_UNIVERSAL_LICENSE_KEY_FILE,
    and optionally AI_RESPONDER_ALLOWED_SENDERS.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_mail_responder import main

if __name__ == "__main__":
    main()
