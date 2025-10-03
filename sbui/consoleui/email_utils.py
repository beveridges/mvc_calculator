import smtplib, ssl
from datetime import datetime
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import os
import logging

SENDER_EMAIL = "support@moviolabs.com"
RECIPIENT_EMAIL = "support@moviolabs.com"   # all logs go here
APP_PASSWORD = "aMJi4826bV."  
SMTP_SERVER = "mail.moviolabs.com"
SMTP_PORT = 465  # SSL

def email_file(filepath,
               recipient=RECIPIENT_EMAIL,
               sender=SENDER_EMAIL,
               password=APP_PASSWORD,
               smtp_server=SMTP_SERVER,
               port=SMTP_PORT):
    """
    Send a file as an email attachment.
    """
    if not os.path.isfile(filepath):
        logging.error(f"email_file: File not found -> {filepath}")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg["Subject"] = f"MVCCalc Session Log — {now}"

    msg.attach(MIMEText("Please find attached the session log.", "plain"))

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
        logging.info(f"Session log emailed to {recipient}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}", exc_info=True)
        return False
