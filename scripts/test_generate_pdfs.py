#!/usr/bin/env python3
"""
Generate PDFs for multiple customers without sending emails.
- Discovers active customers from Odoo
- Generates up to N PDFs (default: 10)
- Saves to output/test-pdfs/
- No emails are sent

Usage:
  python scripts/test_generate_pdfs.py
  python scripts/test_generate_pdfs.py --count 5
  python scripts/test_generate_pdfs.py --week-offset -1
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.odoo import OdooClient
from app.pdf.pdf_generator import generate_customer_pdf
from app.services.window import calculate_reporting_week_with_offset
from app.services.resolve import group_rows_by_customer_id


def discover_customers_with_data(days_back=90, min_hours=1.0):
    """Find customers with timesheet activity."""
    from datetime import date, timedelta
    
    cli = OdooClient()
    if cli.use_stub:
        print("❌ Cannot discover customers in stub mode")
        return {}
    
    end = date.today()
    start = end - timedelta(days=days_back)
    
    uid, models = cli._rpc_authenticate()
    
    # Get all timesheets in period
    domain = [
        ["date", ">=", start.isoformat()],
        ["date", "<=", end.isoformat()]
    ]
    
    timesheets = models.execute_kw(
        cli.db, uid, cli.password,
        "account.analytic.line", "search_read",
        [domain], {"fields": ["partner_id", "unit_amount"]}
    )
    
    # Count hours per customer
    customer_hours = {}
    customer_names = {}
    
    for ts in timesheets:
        partner_info = ts.get("partner_id")
        if partner_info:
            customer_id = str(partner_info[0])
            customer_name = str(partner_info[1])
            hours = float(ts.get("unit_amount", 0))
            
            customer_hours[customer_id] = customer_hours.get(customer_id, 0.0) + hours
            customer_names[customer_id] = customer_name
    
    # Filter by minimum hours and return sorted by hours (descending)
    active_customers = {
        cid: (customer_names[cid], hours) 
        for cid, hours in customer_hours.items() 
        if hours >= min_hours
    }
    
    # Sort by hours descending to get most active customers first
    return dict(sorted(active_customers.items(), key=lambda x: x[1][1], reverse=True))


def main() -> int:
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate test PDFs for multiple customers")
    parser.add_argument("--count", type=int, default=0, help="Number of PDFs to generate (0=all customers with data)")
    parser.add_argument("--week-offset", type=int, default=14, help="Week offset in days (default: 14 = two weeks ago)")
    parser.add_argument("--output-dir", default="output/test-pdfs", help="Output directory")
    parser.add_argument("--days-back", type=int, default=90, help="Days back to search for customer activity (default: 90)")
    args = parser.parse_args()
    
    print("=== PDF GENERATION TEST ===")
    print(f"Target: {'ALL customers with data' if args.count == 0 else f'{args.count} PDFs'}")
    print(f"Week offset: {args.week_offset}")
    print(f"Output: {args.output_dir}")
    print(f"Customer discovery: {args.days_back} days back")
    
    # Calculate reporting week
    week_start, week_end, week_label = calculate_reporting_week_with_offset(args.week_offset)
    print(f"📅 Reporting period: {week_label} ({week_start} – {week_end})")
    
    # Discover customers with broader search
    print(f"\n📊 Discovering customers with timesheet data (last {args.days_back} days)...")
    customers = discover_customers_with_data(days_back=args.days_back, min_hours=0.1)
    
    if not customers:
        print("❌ No customers found with timesheet data")
        print("💡 Try increasing --days-back or check Odoo connection")
        return 1
    
    print(f"✓ Found {len(customers)} customers with activity")
    
    # Show all customers by activity
    print(f"\n🏆 All customers by activity:")
    for i, (cid, (name, hours)) in enumerate(customers.items(), 1):
        print(f"  {i:2d}. {name}: {hours:.1f}h (ID: {cid})")
    
    # Take all customers or limit by count
    if args.count == 0:
        selected_customers = list(customers.items())
    else:
        selected_customers = list(customers.items())[:args.count]
    
    print(f"\n🎯 Generating PDFs for {len(selected_customers)} customers:")
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Fetch timesheet data and process into customer packets
    print(f"\n📊 Fetching timesheet data for reporting period...")
    cli = OdooClient()
    rows = cli.fetch_timesheet_rows(week_start, week_end)

    if not rows:
        print("❌ No timesheet data found for this reporting period")
        print(f"💡 Try different --week-offset (current: {args.week_offset})")
        return 1

    print(f"✓ Found {len(rows)} timesheet entries for reporting period")

    # Group by customer and filter to selected customers
    customer_packets = group_rows_by_customer_id(rows)
    selected_customer_ids = [cid for cid, _ in selected_customers]
    filtered_packets = {
        cid: packet for cid, packet in customer_packets.items()
        if cid in selected_customer_ids
    }

    print(f"✓ {len(filtered_packets)} customers have data in reporting period")
    print(f"✓ {len(selected_customers) - len(filtered_packets)} customers have no data in reporting period")

    # Generate PDFs
    print(f"\n📄 Generating PDFs...")
    success_count = 0

    for i, (customer_id, (customer_name, total_hours)) in enumerate(selected_customers, 1):
        try:
            print(f"  [{i}/{len(selected_customers)}] {customer_name} ({total_hours:.1f}h total)...", end=" ")

            if customer_id not in filtered_packets:
                print("❌ No timesheet data in reporting period")
                continue

            customer_packet = filtered_packets[customer_id]
            filename = f"{customer_name.replace(' ', '_')}_{week_label}.pdf"
            filepath = output_path / filename

            pdf_bytes = generate_customer_pdf(customer_packet, week_label, str(filepath))

            file_size = filepath.stat().st_size / 1024  # KB
            print(f"✓ ({file_size:.1f} KB)")
            success_count += 1

        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ GENERATION COMPLETE")
    print(f"   📁 Output directory: {output_path.absolute()}")
    print(f"   📄 Generated: {success_count}/{len(selected_customers)} PDFs")
    print(f"   📊 Customers with historical data: {len(customers)}")
    print(f"   📊 Customers with data in reporting period: {len(filtered_packets)}")
    
    if success_count > 0:
        print(f"   💡 No emails were sent (PDF-only mode)")
    
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


