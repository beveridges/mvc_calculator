import smtplib, ssl
from datetime import datetime
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import os
import logging

SENDER_EMAIL = "support@moviolabs.com"
RECIPIENT_EMAIL = "telemetry@moviolabs.com"   # telemetry mailbox
APP_PASSWORD = "aMJi4826bV."  
SMTP_SERVER = "mail.moviolabs.com"
SMTP_PORT = 465  # SSL


def send_email(subject,
               body,
               attachments=None,
               recipient=RECIPIENT_EMAIL,
               sender=SENDER_EMAIL,
               password=APP_PASSWORD,
               smtp_server=SMTP_SERVER,
               port=SMTP_PORT):
    """
    Send an email with optional attachments.
    """
    attachments = attachments or []

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    for filepath in attachments:
        if not os.path.isfile(filepath):
            logging.warning(f"send_email: Attachment not found -> {filepath}")
            continue
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(filepath)}"
            )
            msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        logging.debug(f"Email sent to {recipient} ({subject})")
        return True
    except Exception:
        # Fail silently when offline or SMTP unavailable
        logging.debug(f"Email '{subject}' could not be sent (silenced).")
        return False


def email_file(filepath,
               recipient=RECIPIENT_EMAIL,
               sender=SENDER_EMAIL,
               password=APP_PASSWORD,
               smtp_server=SMTP_SERVER,
               port=SMTP_PORT):
    """
    Backwards-compatible helper that sends a single file attachment
    with a standard subject/body.
    """
    if not os.path.isfile(filepath):
        logging.error(f"email_file: File not found -> {filepath}")
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"MVCCalc Session Log — {now}"
    body = "Please find attached the session log."

    return send_email(
        subject=subject,
        body=body,
        attachments=[filepath],
        recipient=recipient,
        sender=sender,
        password=password,
        smtp_server=smtp_server,
        port=port,
    )
