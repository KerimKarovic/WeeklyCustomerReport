#!/usr/bin/env python3
"""
Test email recipient resolution for customer reports.
Shows which customers would get PDFs and which emails they'd be sent to.

Usage:
  python scripts/test_email_recipients.py
  python scripts/test_email_recipients.py --week-offset 14 --count 10
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.odoo import OdooClient
from app.services.window import calculate_reporting_week_with_offset
from app.services.resolve import group_rows_by_customer_id, attach_recipient_emails_from_project_followers


def main() -> int:
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Test email recipient resolution")
    parser.add_argument("--count", type=int, default=10, help="Number of customers to test (default: 10)")
    parser.add_argument("--week-offset", type=int, default=14, help="Week offset in days (default: 14)")
    args = parser.parse_args()
    
    print("=== EMAIL RECIPIENT TEST ===")
    print(f"Testing {args.count} customers")
    print(f"Week offset: {args.week_offset} days")
    
    # Calculate reporting week
    week_start, week_end, week_label = calculate_reporting_week_with_offset(args.week_offset)
    print(f"📅 Reporting period: {week_label} ({week_start} – {week_end})")
    
    # Fetch timesheet data
    print(f"\n📊 Fetching timesheet data...")
    cli = OdooClient()
    print(f"🔗 Odoo mode: {'STUB (samples)' if cli.use_stub else 'REAL (XML-RPC)'}")
    
    rows = cli.fetch_timesheet_rows(week_start, week_end, project_ids=[])
    
    if not rows:
        print("❌ No timesheet data found for this reporting period")
        return 1
    
    print(f"✓ Found {len(rows)} timesheet entries")
    
    # Group by customer
    customer_packets = group_rows_by_customer_id(rows)
    print(f"✓ {len(customer_packets)} customers have data in reporting period")
    
    # Take first N customers for testing
    test_customers = list(customer_packets.items())[:args.count]
    
    # Resolve email recipients
    print(f"\n📧 Resolving email recipients...")
    attach_recipient_emails_from_project_followers(customer_packets, cli)
    
    print(f"\n🎯 EMAIL RECIPIENT ANALYSIS ({len(test_customers)} customers):")
    print("=" * 80)
    
    for i, (customer_id, packet) in enumerate(test_customers, 1):
        customer_name = packet['customer_name']
        project_ids = packet['project_ids']
        recipients = packet['recipients']
        total_hours = sum(row.hours for row in packet['rows'])
        
        print(f"\n{i:2d}. 👤 {customer_name}")
        print(f"    📊 Customer ID: {customer_id}")
        print(f"    ⏱️  Total hours: {total_hours:.1f}h ({len(packet['rows'])} entries)")
        print(f"    📁 Projects: {len(project_ids)} → {', '.join(project_ids) if project_ids else 'None'}")
        
        if recipients:
            print(f"    ✅ Recipients ({len(recipients)}):")
            for email in recipients:
                print(f"       📧 {email}")
            print(f"    📄 PDF would be generated: YES")
            print(f"    📤 Email would be sent: YES")
        else:
            print(f"    ❌ Recipients: None found")
            print(f"    📄 PDF would be generated: YES")
            print(f"    📤 Email would be sent: NO (no recipients)")
        
        print(f"    {'-' * 60}")
    
    # Summary
    customers_with_recipients = sum(1 for _, packet in test_customers if packet['recipients'])
    customers_without_recipients = len(test_customers) - customers_with_recipients
    
    print(f"\n📋 SUMMARY:")
    print(f"   ✅ Customers with recipients: {customers_with_recipients}/{len(test_customers)}")
    print(f"   ❌ Customers without recipients: {customers_without_recipients}/{len(test_customers)}")
    print(f"   📄 PDFs that would be generated: {len(test_customers)}")
    print(f"   📤 Emails that would be sent: {customers_with_recipients}")
    
    if customers_without_recipients > 0:
        print(f"\n💡 Customers without recipients won't receive emails")
        print(f"💡 Check project follower configuration in Odoo")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())