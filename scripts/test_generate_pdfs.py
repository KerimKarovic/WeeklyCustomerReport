#!/usr/bin/env python3
"""
Generate PDFs for multiple customers without sending emails.
- Fetches timesheet data for reporting period
- Generates up to N PDFs (default: 10)
- Saves to output/test-pdfs/
- No emails are sent

Usage:
  python scripts/test_generate_pdfs.py
  python scripts/test_generate_pdfs.py --count 5
  python scripts/test_generate_pdfs.py --week-offset 14
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.odoo import OdooClient
from app.pdf.pdf_generator import generate_customer_pdf
from app.services.window import calculate_reporting_week_with_offset
from app.services.resolve import group_rows_by_customer_id


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate test PDFs for multiple customers")
    parser.add_argument("--count", type=int, default=10, help="Number of PDFs to generate (default: 10)")
    parser.add_argument("--week-offset", type=int, default=14, help="Week offset in days (default: 14)")
    parser.add_argument("--output-dir", default="output/test-pdfs", help="Output directory")
    args = parser.parse_args()

    print("=== PDF GENERATION TEST ===")
    print(f"Target: {args.count} PDFs")
    print(f"Week offset: {args.week_offset} days")
    print(f"Output: {args.output_dir}")

    # Calculate reporting week
    week_start, week_end, week_label = calculate_reporting_week_with_offset(args.week_offset)
    print(f"📅 Reporting period: {week_label} ({week_start} – {week_end})")

    # Fetch timesheet data
    print(f"\n📊 Fetching timesheet data...")
    cli = OdooClient()
    rows = cli.fetch_timesheet_rows(week_start, week_end)

    if not rows:
        print("❌ No timesheet data found for this reporting period")
        print(f"💡 Try different --week-offset (current: {args.week_offset})")
        return 1

    print(f"✓ Found {len(rows)} timesheet entries")

    # Group by customer
    customer_packets = group_rows_by_customer_id(rows)
    print(f"✓ {len(customer_packets)} customers have data in reporting period")

    # Take first N customers
    selected_customers = list(customer_packets.items())[:args.count]
    print(f"\n🎯 Generating PDFs for {len(selected_customers)} customers:")

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate PDFs
    print(f"\n📄 Generating PDFs...")
    success_count = 0

    for i, (customer_id, customer_packet) in enumerate(selected_customers, 1):
        try:
            customer_name = customer_packet['customer_name']
            total_hours = sum(row.hours for row in customer_packet['rows'])
            print(f"  [{i}/{len(selected_customers)}] {customer_name} ({total_hours:.1f}h)...", end=" ")

            filename = f"Arbeitszeitreport_{customer_name.replace(' ', '_')}_{week_label.replace(' ', '_')}.pdf"
            filepath = output_path / filename

            generate_customer_pdf(customer_packet, week_label, str(filepath))

            file_size = filepath.stat().st_size / 1024  # KB
            print(f"✓ ({file_size:.1f} KB)")
            success_count += 1

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n✅ GENERATION COMPLETE")
    print(f"   📁 Output directory: {output_path.absolute()}")
    print(f"   📄 Generated: {success_count}/{len(selected_customers)} PDFs")

    if success_count > 0:
        print(f"   💡 No emails were sent (PDF-only mode)")

    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


