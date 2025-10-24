#!/usr/bin/env python3
"""
Send a simple test email using app.email.sender.send_report_email
- Uses EMAIL_FORWARD_ALL_TO if set (safe)
- Subject/body can be overridden via CLI args

Usage examples:
  python scripts/test_send_email.py
  python scripts/test_send_email.py --subject "Hello" --body "This is a test"
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email.sender import send_report_email


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Send a simple test email")
    parser.add_argument("--subject", default="Testnachricht – Systemcheck", help="Email subject")
    parser.add_argument("--body", default=(
        "Dies ist eine Testnachricht, um die SMTP-Konfiguration zu prüfen.\n\n"
        "Wenn EMAIL_FORWARD_ALL_TO gesetzt ist, geht diese Mail nur an diese Adresse."
    ))
    args = parser.parse_args()

    # Use a safe dummy recipient list; sender will override with EMAIL_FORWARD_ALL_TO if set
    recipients = [os.getenv("EMAIL_FROM_ADDRESS", "noreply@example.com")]

    ok, msg = send_report_email(
        subject=args.subject,
        body_text=args.body,
        recipients=recipients,
    )

    print(("SUCCESS:" if ok else "FAIL:"), msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

