#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration file for auto-license email handler.
Stores settings for IMAP connection, license generation, and email sending.
"""

import os
from pathlib import Path

# IMAP Settings (for receiving emails)
IMAP_SERVER = "mail.moviolabs.com"
IMAP_PORT = 993  # SSL
IMAP_USERNAME = "support@moviolabs.com"
IMAP_PASSWORD = os.getenv("SUPPORT_EMAIL_PASSWORD")  # From environment variable

# License Settings
DEFAULT_COUNTRY = "DE"  # For @hfmdd.de users
DEFAULT_EXPIRATION_DAYS = 0  # No expiration (0 = no expiration)
USE_WILDCARD_HWID = True  # For @hfmdd.de users (allows license on any machine)

# Processing Settings
POLL_INTERVAL_SECONDS = 60  # Check for new emails every minute
PROCESSED_FOLDER = "Processed_Licenses"  # IMAP folder to move processed emails
PROCESSED_EMAILS_DB = "processed_emails.json"  # Track processed emails (local file)

# Non-@hfmdd.de Email Handling
# Options: "leave_unread", "mark_read", "move_to_folder"
NON_HFMDD_EMAIL_ACTION = "leave_unread"  # Leave unread so you can easily see emails that need manual processing
NON_HFMDD_EMAIL_FOLDER = "Manual_Review"  # Folder to move non-@hfmdd.de emails (if action is "move_to_folder")

# Email Settings (for sending licenses)
SMTP_SERVER = "mail.moviolabs.com"
SMTP_PORT = 465  # SSL
SMTP_USERNAME = "support@moviolabs.com"
SMTP_PASSWORD = os.getenv("SUPPORT_EMAIL_PASSWORD")  # From environment variable

# Logging
LOG_FILE = "auto_license_handler.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Script directory (for relative paths)
SCRIPT_DIR = Path(__file__).parent

# Paths
PROCESSED_EMAILS_DB_PATH = SCRIPT_DIR / PROCESSED_EMAILS_DB
LOG_FILE_PATH = SCRIPT_DIR / LOG_FILE
EMAIL_TEMPLATE_PATH = SCRIPT_DIR / "license_email_template.txt"

