#!/usr/bin/env python3
"""
Send email with real generated PDF using existing customer data.
- Uses EMAIL_FORWARD_ALL_TO for safe delivery during testing
- Generates PDF from real timesheet data
- Tests email formatting and delivery

Usage:
  python scripts/test_send_with_attachment.py
  python scripts/test_send_with_attachment.py --project-id 15 --week-offset 14
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email.sender import send_report_email
from app.pdf.pdf_generator import generate_customer_pdf
from app.services.resolve import group_rows_by_customer_id
from app.services.window import calculate_reporting_week_with_offset
from app.clients.odoo import OdooClient


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Send email with real PDF attachment")
    parser.add_argument("--subject", default="Arbeitszeitreport Test", help="Email subject")
    parser.add_argument("--project-id", default="1", help="Project ID to use (default: 1)")
    parser.add_argument("--week-offset", type=int, default=14, help="Week offset in days (default: 14)")
    args = parser.parse_args()

    # Calculate reporting week
    week_start, week_end, week_label = calculate_reporting_week_with_offset(args.week_offset)
    print(f"📅 Using reporting period: {week_label}")

    # Fetch real timesheet data
    print(f"📊 Fetching timesheet data for project {args.project_id}...")
    cli = OdooClient()
    rows = cli.fetch_timesheet_rows(week_start, week_end, project_ids=[args.project_id])

    if not rows:
        print(f"❌ No timesheet data found for project {args.project_id}")
        print("💡 Try different --project-id or --week-offset")
        return 1

    # Group by customer and select first one
    customer_packets = group_rows_by_customer_id(rows)

    if not customer_packets:
        print("❌ No customers found in data")
        return 1

    # Use first customer
    customer_id, customer_packet = next(iter(customer_packets.items()))
    print(f"✓ Found {len(customer_packet['rows'])} entries for {customer_packet['customer_name']}")

    # Create output directory
    out_dir = Path("output/email-test")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate PDF
    print("📄 Generating PDF...")
    try:
        pdf_path = out_dir / f"Arbeitszeitreport_{customer_packet['customer_name'].replace(' ', '_')}_{week_label.replace(' ', '_')}.pdf"
        pdf_bytes = generate_customer_pdf(customer_packet, week_label, str(pdf_path))
        print(f"✓ Generated PDF: {pdf_path.name} ({len(pdf_bytes)} bytes)")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return 1

    # Create email body
    total_hours = sum(row.hours for row in customer_packet["rows"])
    email_body = f"""Sehr geehrte Damen und Herren,

anbei erhalten Sie den Arbeitszeitreport für {customer_packet['customer_name']} für {week_label}.

Zusammenfassung:
• Gesamtstunden: {total_hours:.1f}h
• Anzahl Einträge: {len(customer_packet['rows'])}
• Projekte: {len(customer_packet['project_ids'])}

Der detaillierte Report ist als PDF-Anhang beigefügt.

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
KIRATIK GmbH

---
Diese E-Mail wurde automatisch generiert.
"""

    # Send email
    print("📧 Sending email...")
    ok, msg = send_report_email(
        subject=args.subject,
        body_text=email_body,
        recipients=["test@example.com"],
        attachment_paths=[(pdf_path.name, str(pdf_path))],
    )

    print(("SUCCESS:" if ok else "FAIL:"), msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

