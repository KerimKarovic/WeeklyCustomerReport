from __future__ import annotations
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, Sequence, Tuple


def _parse_bool(value: str | None, default: bool = False) -> bool:
    v = (value or "").strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default


def send_report_email(
    subject: str,
    body_text: str,
    recipients: Sequence[str],
    *,
    attachment_paths: Optional[Sequence[Tuple[str, str]]] = None,  # (filename, path)
) -> Tuple[bool, str]:
    """
    Send a plain-text email with optional PDF attachments using SMTP.

    Environment variables used:
    - EMAIL_SMTP_HOST, EMAIL_SMTP_PORT
    - EMAIL_SMTP_STARTTLS (true/false)
    - EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
    - EMAIL_FROM_ADDRESS
    - EMAIL_REPLY_TO (optional)
    - EMAIL_FORWARD_ALL_TO (optional, overrides recipients for safe testing)

    Returns: (success, message)
    """
    host = os.getenv("EMAIL_SMTP_HOST", "localhost")
    port = int(os.getenv("EMAIL_SMTP_PORT", "25"))
    use_starttls = _parse_bool(os.getenv("EMAIL_SMTP_STARTTLS"), default=False)
    username = os.getenv("EMAIL_SMTP_USERNAME", "").strip()
    password = os.getenv("EMAIL_SMTP_PASSWORD", "").strip()
    from_addr = os.getenv("EMAIL_FROM_ADDRESS", "noreply@example.com").strip()
    reply_to = os.getenv("EMAIL_REPLY_TO", from_addr).strip()

    forward_all = os.getenv("EMAIL_FORWARD_ALL_TO", "").strip()
    if forward_all:
        recipients = [forward_all]

    # Basic validation
    to_addrs = [r for r in recipients if r and "@" in r]
    if not to_addrs:
        return False, "No valid recipients"

    # Build the email
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body_text, _subtype="plain", _charset="utf-8"))

    # Attach files
    for fname, path in (attachment_paths or []):
        try:
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=fname)
                msg.attach(part)
        except FileNotFoundError:
            return False, f"Attachment not found: {path}"
        except Exception as exc:
            return False, f"Failed to attach {path}: {exc}"

    # Send
    context = ssl.create_default_context()

    try:
        if use_starttls:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                if username:
                    server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
        elif port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
                if username:
                    server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                if username:
                    server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
    except Exception as exc:
        return False, f"SMTP send failed: {exc}"

    return True, f"Sent to {len(to_addrs)} recipient(s)"
