import smtplib, ssl
from datetime import datetime
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import logging
import os

SENDER_EMAIL = "moviolabs@gmail.com"
RECIPIENT_EMAIL = "moviolabs@gmail.com" 
APP_PASSWORD = "edmx kaow bief lkay"          


def email_file(filepath, recipient, sender, password,
               smtp_server="smtp.gmail.com", port=465):
    """
    Send a file as an email attachment.

    Args:
        filepath (str): Path to file to attach.
        recipient (str): Email recipient.
        sender (str): Email sender (must match login).
        password (str): SMTP or App Password.
        smtp_server (str): SMTP server host (default: Gmail).
        port (int): Port for SMTP SSL (default: 465).
    """
    if not os.path.isfile(filepath):
        logging.error(f"email_file: File not found -> {filepath}")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg["Subject"] = f"MOTUS Session Log — {now}"
    

    # Body
    msg.attach(MIMEText("Please find attached the session log.", "plain"))

    # Attach file
    with open(filepath, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(filepath)}"
        )
        msg.attach(part)

    # Send email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        logging.info(f"Session log emailed to {recipient}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}", exc_info=True)
        return False
