"""Email alert sender. Reads SMTP configuration from environment variables."""

from email.message import EmailMessage
from os import getenv
import smtplib

EMAIL_SERVER = getenv("EMAIL_SERVER")
SENDER = getenv("SENDER")
RECIPIENT = getenv("RECIPIENT")
SUBJECT_PREFIX = "[Castle]: "


def send_email(subject_text: str, body_text: str):
    """Send a plain-text email. Subject is prefixed with SUBJECT_PREFIX."""
    msg = EmailMessage()
    msg.set_content(body_text)
    msg["Subject"] = f"{SUBJECT_PREFIX}{subject_text}"
    msg["From"] = SENDER
    msg["To"] = RECIPIENT

    s = smtplib.SMTP(EMAIL_SERVER)
    s.send_message(msg)
    s.quit()
