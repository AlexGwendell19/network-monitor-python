# =============================================================
#  alerts.py — Email Alert Module
#  Author: Rodrigo Alexis Guerra Wendell
# =============================================================

import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config


def send_alert(host_label: str, host_ip: str, event: str) -> bool:
    """
    Send an email alert when a host goes DOWN or comes back UP.

    Args:
        host_label: Human-readable name (e.g. "HTTP Server")
        host_ip:    IP address of the host
        event:      "DOWN" or "UP"

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not config.EMAIL_ENABLED:
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji     = "🔴" if event == "DOWN" else "🟢"
    subject   = f"[Network Monitor] {emoji} {host_label} is {event}"

    body = f"""
Network Monitor Alert
=====================
Host    : {host_label} ({host_ip})
Status  : {event}
Time    : {timestamp}
Machine : {socket.gethostname()}

{"⚠️  Host is not responding to ping." if event == "DOWN"
 else "✅  Host has recovered and is responding again."}

-- 
Network Monitor | Rodrigo Alexis Guerra Wendell
"""

    msg = MIMEMultipart()
    msg["From"]    = config.EMAIL_SENDER
    msg["To"]      = config.EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECEIVER, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        print("  [ALERT ERROR] Gmail authentication failed. Check EMAIL_PASSWORD in config.py.")
        print("  Tip: Use a Gmail App Password, not your account password.")
        print("  Guide: https://support.google.com/accounts/answer/185833")
        return False
    except Exception as e:
        print(f"  [ALERT ERROR] Could not send email: {e}")
        return False
