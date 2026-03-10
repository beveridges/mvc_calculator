#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration for AI Mail Responder.

Secrets (MAILBOX_PASS, OPENAI_API_KEY, UNIVERSAL_LICENSE_KEY) should be set
via environment variables. Optional: store UNIVERSAL_LICENSE_KEY in a file
and set UNIVERSAL_LICENSE_KEY_FILE to its path.
"""

import os
from pathlib import Path

# Script directory (for relative paths)
SCRIPT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# IMAP (incoming mail)
# ---------------------------------------------------------------------------
IMAP_HOST = os.getenv("AI_RESPONDER_IMAP_HOST", "mail.moviolabs.com")
IMAP_PORT = int(os.getenv("AI_RESPONDER_IMAP_PORT", "993"))
IMAP_USE_SSL = os.getenv("AI_RESPONDER_IMAP_SSL", "true").lower() in ("1", "true", "yes")
IMAP_FOLDER = os.getenv("AI_RESPONDER_IMAP_FOLDER", "INBOX")

MAILBOX_USER = os.getenv("AI_RESPONDER_MAILBOX_USER", "marilin.rojas@moviolabs.com")
MAILBOX_PASS = os.getenv("AI_RESPONDER_MAILBOX_PASS", "")  # Required; set in env

# ---------------------------------------------------------------------------
# SMTP (outgoing replies)
# ---------------------------------------------------------------------------
SMTP_HOST = os.getenv("AI_RESPONDER_SMTP_HOST", "mail.moviolabs.com")
SMTP_PORT = int(os.getenv("AI_RESPONDER_SMTP_PORT", "587"))
SMTP_USE_STARTTLS = True  # 587 typically uses STARTTLS

# ---------------------------------------------------------------------------
# OpenAI (first-reply generation)
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("AI_RESPONDER_OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("AI_RESPONDER_OPENAI_MODEL", "gpt-4.1-mini")

# ---------------------------------------------------------------------------
# License key (appended to first reply; AI never sees it)
# Set UNIVERSAL_LICENSE_KEY in env, or UNIVERSAL_LICENSE_KEY_FILE to path to a file containing the key.
# ---------------------------------------------------------------------------
UNIVERSAL_LICENSE_KEY = os.getenv("AI_RESPONDER_UNIVERSAL_LICENSE_KEY", "")
UNIVERSAL_LICENSE_KEY_FILE = os.getenv("AI_RESPONDER_UNIVERSAL_LICENSE_KEY_FILE", "")

def get_universal_license_key() -> str:
    """Return the universal license key from env or from file."""
    if UNIVERSAL_LICENSE_KEY.strip():
        return UNIVERSAL_LICENSE_KEY.strip()
    if UNIVERSAL_LICENSE_KEY_FILE.strip():
        p = Path(UNIVERSAL_LICENSE_KEY_FILE.strip())
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return ""

# ---------------------------------------------------------------------------
# Allowed senders (whitelist; only these get auto-replies)
# ---------------------------------------------------------------------------
_ALLOWED_SENDERS_ENV = os.getenv("AI_RESPONDER_ALLOWED_SENDERS", "")
# Comma-separated list in env, e.g. "a@b.com, c@d.de"
if _ALLOWED_SENDERS_ENV.strip():
    ALLOWED_SENDERS = {s.strip().lower() for s in _ALLOWED_SENDERS_ENV.split(",") if s.strip()}
else:
    # Default if not set in env
    ALLOWED_SENDERS = {
        "gerard.madden@hfmdd.de",
        "scottwbeveridge@gmail.com",
    }

# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------
POLL_SECONDS = int(os.getenv("AI_RESPONDER_POLL_SECONDS", "60"))
SECOND_REPLY_WINDOW_SECONDS = 24 * 60 * 60  # 24 hours

# ---------------------------------------------------------------------------
# State and logging
# ---------------------------------------------------------------------------
DB_PATH = SCRIPT_DIR / os.getenv("AI_RESPONDER_DB_NAME", "ai_mail_state.db")
LOG_FILE = SCRIPT_DIR / os.getenv("AI_RESPONDER_LOG_FILE", "ai_mail_responder.log")
LOG_LEVEL = os.getenv("AI_RESPONDER_LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Templates (overridable via env or keep defaults)
# ---------------------------------------------------------------------------
SECOND_REPLY_TEMPLATE = (
    "Thanks for following up.\n\n"
    "I'm currently looking into this and will get back to you shortly."
)

SYSTEM_PROMPT = (
    "You are a professional, concise software technical support agent.\n"
    "Write an email reply to the customer based on their message.\n"
    "Rules:\n"
    "- Do not mention AI or automation.\n"
    "- Do not include any license keys (the system will add it separately).\n"
    "- Do not overpromise. If unsure, ask one clear follow-up question.\n"
    "- Keep it short, calm, and helpful.\n"
)

def first_reply_footer(license_key: str) -> str:
    """Build the footer appended to the first reply (includes license key)."""
    return (
        "\n\nUniversal License Key:\n"
        f"{license_key}\n\n"
        "If it still doesn't work, please tell me:\n"
        "1) the exact error message you see\n"
        "2) your app version\n"
        "3) your OS (Windows/macOS/Linux)\n"
    )
