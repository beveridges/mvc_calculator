#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-License Email Handler for @hfmdd.de Users

Monitors incoming emails to support@moviolabs.com and automatically generates
and sends license keys to @hfmdd.de email addresses.

Usage:
    python auto_license_email_handler.py

The script runs continuously, polling for new emails every 60 seconds.
"""

import imaplib
import email
import json
import logging
import time
import sys
from pathlib import Path
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add parent directory to path to import utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from utilities.license import generate_license_key, WILDCARD_HWID_HFMDD
from sbui.consoleui.email_utils import send_email
import auto_license_config as config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_processed_emails() -> Dict[str, datetime]:
    """Load list of processed email addresses with timestamps."""
    if not config.PROCESSED_EMAILS_DB_PATH.exists():
        return {}
    
    try:
        with open(config.PROCESSED_EMAILS_DB_PATH, 'r') as f:
            data = json.load(f)
            # Convert timestamp strings back to datetime objects (stored as ISO strings)
            return {email: datetime.fromisoformat(ts) for email, ts in data.items()}
    except Exception as e:
        logger.error(f"Error loading processed emails: {e}")
        return {}


def save_processed_emails(processed: Dict[str, datetime]):
    """Save list of processed email addresses with timestamps."""
    try:
        # Convert datetime objects to ISO strings for JSON serialization
        data = {email: ts.isoformat() for email, ts in processed.items()}
        with open(config.PROCESSED_EMAILS_DB_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed emails: {e}")


def is_hfmdd_email(email_address: str) -> bool:
    """Check if email address is from @hfmdd.de domain."""
    if not email_address or "@" not in email_address:
        return False
    domain = email_address.split("@")[-1].lower()
    return domain == "hfmdd.de"


def extract_sender_email(email_msg: email.message.Message) -> Optional[str]:
    """Extract sender email address from email message."""
    try:
        from_header = email_msg.get("From", "")
        if not from_header:
            return None
        
        # Decode header if needed
        decoded_header = decode_header(from_header)[0]
        if isinstance(decoded_header[0], bytes):
            from_header = decoded_header[0].decode(decoded_header[1] or 'utf-8')
        else:
            from_header = decoded_header[0]
        
        # Extract email address (handle "Name <email@domain.com>" format)
        if "<" in from_header and ">" in from_header:
            start = from_header.index("<") + 1
            end = from_header.index(">")
            email_addr = from_header[start:end].strip()
        else:
            email_addr = from_header.strip()
        
        return email_addr.lower()
    except Exception as e:
        logger.error(f"Error extracting sender email: {e}")
        return None


def is_already_processed(sender_email: str, processed_emails: Dict[str, datetime], 
                         cooldown_hours: int = 24) -> bool:
    """
    Check if email has already been processed.
    
    Args:
        sender_email: Sender's email address
        processed_emails: Dictionary of processed emails
        cooldown_hours: Hours to wait before allowing another license for same email
    
    Returns:
        True if already processed within cooldown period
    """
    if sender_email not in processed_emails:
        return False
    
    last_processed = processed_emails[sender_email]
    hours_since = (datetime.now() - last_processed).total_seconds() / 3600
    
    if hours_since < cooldown_hours:
        logger.info(f"Email {sender_email} already processed {hours_since:.1f} hours ago (cooldown: {cooldown_hours}h)")
        return True
    
    return False


def generate_license_for_email(sender_email: str) -> Optional[str]:
    """
    Generate a license key for the given email address.
    
    Args:
        sender_email: Email address to generate license for
    
    Returns:
        License key string or None if generation failed
    """
    try:
        license_key = generate_license_key(
            email=sender_email,
            country=config.DEFAULT_COUNTRY,
            hwid=WILDCARD_HWID_HFMDD,  # Will be replaced by wildcard in function
            expiration_days=config.DEFAULT_EXPIRATION_DAYS,
            use_wildcard_hwid=config.USE_WILDCARD_HWID
        )
        logger.info(f"Generated license for {sender_email}")
        return license_key
    except Exception as e:
        logger.error(f"Error generating license for {sender_email}: {e}")
        return None


def load_email_template() -> str:
    """Load email template from file."""
    try:
        if config.EMAIL_TEMPLATE_PATH.exists():
            template = config.EMAIL_TEMPLATE_PATH.read_text(encoding='utf-8')
            return template
        else:
            logger.warning(f"Email template not found at {config.EMAIL_TEMPLATE_PATH}, using default")
            return get_default_email_template()
    except Exception as e:
        logger.error(f"Error loading email template: {e}, using default")
        return get_default_email_template()


def get_default_email_template() -> str:
    """Get default email template if file not found."""
    return """Subject: Your MVC Calculator License Key

Dear Customer,

Thank you for your license request. Your license key is provided below.

LICENSE KEY:
{LICENSE_KEY}

INSTALLATION INSTRUCTIONS:

1. Copy the license key above
2. Create a file named "license.key" 
3. Paste the license key into the file
4. Save the file to one of these locations:
   - Windows: %APPDATA%\\MVC_Calculator\\license.key
   - Or in the same folder as the MVC Calculator executable

The license key is valid for your @hfmdd.de email address and will work on any machine.

If you need assistance, please contact support@moviolabs.com

Best regards,
MVC Calculator Support Team"""


def format_email_body(template: str, license_key: str) -> Tuple[str, str]:
    """
    Format email template with license key.
    
    Returns:
        (subject, body) tuple
    """
    # Split template into subject and body
    lines = template.split('\n')
    subject = "Your MVC Calculator License Key"
    body_lines = []
    
    in_body = False
    for line in lines:
        if line.startswith("Subject:"):
            subject = line.replace("Subject:", "").strip()
        elif line.startswith("Dear") or in_body:
            in_body = True
            body_lines.append(line)
        elif not line.strip():
            body_lines.append(line)
    
    body = '\n'.join(body_lines)
    body = body.replace("{LICENSE_KEY}", license_key)
    
    return subject, body


def send_license_email(recipient_email: str, license_key: str) -> bool:
    """
    Send license key to recipient via email.
    
    Args:
        recipient_email: Email address to send license to
        license_key: License key to send
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Load and format email template
        template = load_email_template()
        subject, body = format_email_body(template, license_key)
        
        # Send email
        try:
            success = send_email(
                subject=subject,
                body=body,
                recipient=recipient_email,
                sender=config.SMTP_USERNAME,
                password=config.SMTP_PASSWORD,
                smtp_server=config.SMTP_SERVER,
                port=config.SMTP_PORT
            )
            
            if success:
                logger.info(f"License email sent successfully to {recipient_email}")
            else:
                logger.error(f"Failed to send license email to {recipient_email} (send_email returned False)")
            
            return success
        except Exception as e:
            logger.error(f"Exception while sending license email to {recipient_email}: {e}", exc_info=True)
            return False
    except Exception as e:
        logger.error(f"Error sending license email to {recipient_email}: {e}")
        return False


def connect_imap() -> Optional[imaplib.IMAP4_SSL]:
    """Connect to IMAP server."""
    try:
        if not config.IMAP_PASSWORD:
            logger.error("IMAP_PASSWORD not set in environment variable SUPPORT_EMAIL_PASSWORD")
            return None
        
        logger.info(f"Connecting to IMAP server {config.IMAP_SERVER}:{config.IMAP_PORT}")
        imap = imaplib.IMAP4_SSL(config.IMAP_SERVER, config.IMAP_PORT)
        imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
        logger.info("IMAP connection established")
        return imap
    except Exception as e:
        logger.error(f"Error connecting to IMAP server: {e}")
        return None


def get_unread_emails(imap: imaplib.IMAP4_SSL) -> List[Tuple[str, email.message.Message]]:
    """
    Get all unread emails from inbox.
    
    Returns:
        List of (email_id, email_message) tuples
    """
    try:
        imap.select("INBOX")
        status, messages = imap.search(None, "UNSEEN")
        
        if status != "OK":
            logger.warning("Failed to search for unread emails")
            return []
        
        email_ids = messages[0].split()
        emails = []
        
        for email_id in email_ids:
            try:
                status, msg_data = imap.fetch(email_id, "(RFC822)")
                if status == "OK":
                    email_body = msg_data[0][1]
                    email_msg = email.message_from_bytes(email_body)
                    emails.append((email_id.decode(), email_msg))
            except Exception as e:
                logger.error(f"Error fetching email {email_id}: {e}")
        
        return emails
    except Exception as e:
        logger.error(f"Error getting unread emails: {e}")
        return []


def handle_non_hfmdd_email(imap: imaplib.IMAP4_SSL, email_id: str):
    """
    Handle emails that are not from @hfmdd.de domain.
    Actions are configured in auto_license_config.py.
    """
    action = config.NON_HFMDD_EMAIL_ACTION.lower()
    
    try:
        if action == "mark_read":
            # Mark as read so user can see it but inbox stays clean
            imap.store(email_id, '+FLAGS', '\\Seen')
            logger.debug(f"Marked non-@hfmdd.de email {email_id} as read")
        elif action == "move_to_folder":
            # Move to manual review folder
            try:
                imap.create(config.NON_HFMDD_EMAIL_FOLDER)
            except imaplib.IMAP4.error:
                # Folder might already exist, that's okay
                pass
            imap.copy(email_id, config.NON_HFMDD_EMAIL_FOLDER)
            imap.store(email_id, '+FLAGS', '\\Deleted')
            imap.expunge()
            logger.debug(f"Moved non-@hfmdd.de email {email_id} to {config.NON_HFMDD_EMAIL_FOLDER}")
        elif action == "leave_unread":
            # Do nothing - leave email unread in inbox
            logger.debug(f"Left non-@hfmdd.de email {email_id} unread")
        else:
            logger.warning(f"Unknown NON_HFMDD_EMAIL_ACTION: {action}, leaving email unread")
    except Exception as e:
        logger.error(f"Error handling non-@hfmdd.de email {email_id}: {e}")


def mark_email_processed(imap: imaplib.IMAP4_SSL, email_id: str, move_to_folder: bool = True):
    """
    Mark email as processed by moving it to processed folder or marking as read.
    
    Args:
        imap: IMAP connection
        email_id: Email ID to mark as processed
        move_to_folder: If True, move to processed folder; otherwise just mark as read
    """
    try:
        if move_to_folder:
            # Create processed folder if it doesn't exist
            try:
                imap.create(config.PROCESSED_FOLDER)
            except imaplib.IMAP4.error:
                # Folder might already exist, that's okay
                pass
            
            # Copy email to processed folder
            imap.copy(email_id, config.PROCESSED_FOLDER)
            # Mark original as deleted
            imap.store(email_id, '+FLAGS', '\\Deleted')
            imap.expunge()
            logger.debug(f"Email {email_id} moved to {config.PROCESSED_FOLDER}")
        else:
            # Just mark as read
            imap.store(email_id, '+FLAGS', '\\Seen')
            logger.debug(f"Email {email_id} marked as read")
    except Exception as e:
        logger.error(f"Error marking email {email_id} as processed: {e}")


def process_email(imap: imaplib.IMAP4_SSL, email_id: str, email_msg: email.message.Message, 
                  processed_emails: Dict[str, datetime]) -> bool:
    """
    Process a single email: check if from @hfmdd.de, generate and send license.
    
    Returns:
        True if email was processed successfully
    """
    # Extract sender email
    sender_email = extract_sender_email(email_msg)
    if not sender_email:
        logger.warning(f"Could not extract sender email from email {email_id}")
        return False
    
    # Check if from @hfmdd.de
    if not is_hfmdd_email(sender_email):
        logger.info(f"Email from {sender_email} is not from @hfmdd.de - requires manual processing")
        # Handle non-@hfmdd.de emails based on configuration
        handle_non_hfmdd_email(imap, email_id)
        return False
    
    logger.info(f"Processing email from {sender_email}")
    
    # Check if already processed
    if is_already_processed(sender_email, processed_emails):
        logger.info(f"Skipping {sender_email} - already processed recently")
        mark_email_processed(imap, email_id, move_to_folder=False)
        return False
    
    # Generate license
    license_key = generate_license_for_email(sender_email)
    if not license_key:
        logger.error(f"Failed to generate license for {sender_email}")
        return False
    
    # Send license email
    if not send_license_email(sender_email, license_key):
        logger.error(f"Failed to send license email to {sender_email}")
        return False
    
    # Mark as processed
    processed_emails[sender_email] = datetime.now()
    save_processed_emails(processed_emails)
    mark_email_processed(imap, email_id, move_to_folder=True)
    
    logger.info(f"Successfully processed email from {sender_email}")
    return True


def main_loop():
    """Main processing loop - runs continuously."""
    logger.info("Starting auto-license email handler")
    logger.info(f"Polling interval: {config.POLL_INTERVAL_SECONDS} seconds")
    
    processed_emails = load_processed_emails()
    logger.info(f"Loaded {len(processed_emails)} previously processed emails")
    
    imap = None
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        try:
            # Connect to IMAP if not connected
            if imap is None:
                imap = connect_imap()
                if imap is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many connection errors ({consecutive_errors}), exiting")
                        break
                    logger.warning(f"Connection failed, retrying in {config.POLL_INTERVAL_SECONDS} seconds...")
                    time.sleep(config.POLL_INTERVAL_SECONDS)
                    continue
                consecutive_errors = 0
            
            # Get unread emails
            unread_emails = get_unread_emails(imap)
            
            if unread_emails:
                logger.info(f"Found {len(unread_emails)} unread email(s)")
            
            # Process each email
            for email_id, email_msg in unread_emails:
                try:
                    process_email(imap, email_id, email_msg, processed_emails)
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
            
            # Wait before next poll
            time.sleep(config.POLL_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"Too many consecutive errors ({consecutive_errors}), exiting")
                break
            time.sleep(config.POLL_INTERVAL_SECONDS)
        finally:
            # Close IMAP connection on exit
            if imap:
                try:
                    imap.close()
                    imap.logout()
                except Exception:
                    pass
    
    logger.info("Auto-license email handler stopped")


if __name__ == "__main__":
    main_loop()

