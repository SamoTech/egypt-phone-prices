import os
import smtplib
from email.message import EmailMessage


def notify_many_failures(failed, total):
    recipient = os.getenv("ALERT_EMAIL")
    if not recipient:
        return

    msg = EmailMessage()
    msg["Subject"] = f"[Prices] High scrape failure rate: {failed}/{total}"
    msg["From"] = recipient
    msg["To"] = recipient
    msg.set_content(
        f"More than 50% of scrapes failed.\nFailed: {failed}\nTotal: {total}\nCheck logs."
    )

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_host or not smtp_user or not smtp_pass:
        return

    with smtplib.SMTP_SSL(smtp_host, 465) as s:
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)
