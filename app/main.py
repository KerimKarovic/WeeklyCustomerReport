#!/usr/bin/env python3
"""
Weekly timesheet report generator for KIRATIK customers.
"""
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

from app.clients.odoo import OdooClient
from app.services.window import calculate_reporting_week_with_offset
from app.services.resolve import group_rows_by_customer_id, attach_recipient_emails_from_project_followers
from app.services.cleanup import cleanup_old_pdfs
from app.services.report_log import ReportLog
from app.pdf.pdf_generator import generate_customer_pdf
from app.email.sender import send_report_email

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate weekly timesheet reports")
    parser.add_argument("--mode", choices=["preview", "customer"], default="customer")
    parser.add_argument("--output-dir", default="output/reports")
    parser.add_argument("--week-offset", type=int, default=14)
    parser.add_argument("--projects", help="Comma-separated project IDs")
    args = parser.parse_args()
    
    # Initialize report log
    report_log = ReportLog()
    
    # Calculate reporting week
    week_start, week_end, week_label = calculate_reporting_week_with_offset(args.week_offset)
    
    # Cleanup old PDFs
    cleanup_old_pdfs(Path(args.output_dir), days=30)
    
    # Fetch data and process customers
    cli = OdooClient()
    rows = cli.fetch_timesheet_rows(week_start, week_end)
    customer_packets = group_rows_by_customer_id(rows)
    attach_recipient_emails_from_project_followers(customer_packets, cli)
    
    # Process each customer
    for customer_id, customer_packet in customer_packets.items():
        customer_name = customer_packet["customer_name"]
        
        # Check if already sent
        if report_log.was_sent(customer_id, week_label):
            print(f"⏭️  {customer_name}: Already sent for {week_label}")
            continue
            
        # Generate PDF
        pdf_filename = f"Arbeitszeitreport_{customer_name.replace(' ', '_')}_{week_label.replace(' ', '_')}.pdf"
        pdf_path = Path(args.output_dir) / pdf_filename
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        generate_customer_pdf(customer_packet, week_label, str(pdf_path))
        
        # Send email if recipients exist
        if customer_packet["recipients"]:
            total_hours = sum(row.hours for row in customer_packet["rows"])
            
            email_body = f"""Sehr geehrte Damen und Herren,

anbei erhalten Sie den Arbeitszeitreport für {customer_name} für {week_label}.

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
            
            ok, msg = send_report_email(
                subject=f"Arbeitszeitreport {customer_name} - {week_label}",
                body_text=email_body,
                recipients=customer_packet["recipients"],
                attachment_paths=[(pdf_filename, str(pdf_path))]
            )
            
            if ok:
                report_log.mark_sent(customer_id, week_label, customer_packet["recipients"], pdf_filename)
                print(f"✅ {customer_name}: Email sent to {len(customer_packet['recipients'])} recipients")
            else:
                print(f"❌ {customer_name}: Email failed - {msg}")
        else:
            print(f"📄 {customer_name}: PDF generated, no recipients")

if __name__ == "__main__":
    main()
