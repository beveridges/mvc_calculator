# -*- coding: utf-8 -*-
"""
Code Signing Configuration
==========================

To enable code signing and prevent Windows SmartScreen warnings:

1. Get a code signing certificate:
   - Purchase from: DigiCert, Sectigo, GlobalSign, etc. (~$200-400/year)
   - Or use a free certificate from: https://letsencrypt.org (limited support)
   
2. Configure one of these options below:

Option A: PFX File (recommended for automated builds)
   - Export your certificate as .pfx file
   - Set CERT_PATH and CERT_PASSWORD below

Option B: Windows Certificate Store
   - Install certificate in Windows Certificate Store
   - Find thumbprint: certlm.msc → Personal → Certificates
   - Set CERT_THUMBPRINT below

3. Uncomment and configure the settings below
"""

# ============================================================================
# CODE SIGNING CONFIGURATION
# ============================================================================

# Enable code signing (set to True when certificate is configured)
ENABLE_CODE_SIGNING = False

# Option A: PFX File Method
CERT_PATH = None  # e.g., r"C:\path\to\certificate.pfx"
CERT_PASSWORD = None  # Password for PFX file

# Option B: Certificate Store Method (by thumbprint)
CERT_THUMBPRINT = None  # e.g., "ABC123DEF456..."

# Timestamp server (prevents signature expiration)
# Common options:
# - http://timestamp.digicert.com (DigiCert)
# - http://timestamp.sectigo.com (Sectigo)
# - http://timestamp.globalsign.com/tsa/r6advanced1 (GlobalSign)
TIMESTAMP_URL = "http://timestamp.digicert.com"

# File description (shown in file properties)
FILE_DESCRIPTION = "MVC Calculator"
FILE_DESCRIPTION_URL = "https://moviolabs.com"

