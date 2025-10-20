#!/usr/bin/env python3
"""
Discover active customers from Odoo timesheets and update .env file.
"""
import os
import sys
from datetime import date, timedelta
from collections import Counter

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.clients.odoo import OdooClient

def discover_active_customers(days_back=90, min_hours=1.0):
    """Find customers with timesheet activity in the last N days."""
    cli = OdooClient()
    
    if cli.use_stub:
        print("❌ Cannot discover customers in stub mode")
        return {}
    
    end = date.today()
    start = end - timedelta(days=days_back)
    
    print(f"Discovering customers from {start} to {end} (min {min_hours}h)...")
    
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
    customer_hours = {}  # Dict[str, float]
    customer_names = {}
    
    for ts in timesheets:
        partner_info = ts.get("partner_id")
        if partner_info:  # Skip entries without customer
            customer_id = str(partner_info[0])
            customer_name = str(partner_info[1])
            hours = float(ts.get("unit_amount", 0))
            
            customer_hours[customer_id] = customer_hours.get(customer_id, 0.0) + hours
            customer_names[customer_id] = customer_name
    
    # Filter by minimum hours
    active_customers = {
        cid: (customer_names[cid], hours) 
        for cid, hours in customer_hours.items() 
        if hours >= min_hours
    }
    
    return active_customers

def update_env_file(customer_ids):
    """Update .env file with discovered customer IDs."""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"❌ {env_path} not found")
        return
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update REPORT_CUSTOMER_IDS line
    customer_ids_str = ",".join(sorted(customer_ids))
    new_line = f"REPORT_CUSTOMER_IDS={customer_ids_str}\n"
    
    # Find and replace the line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("REPORT_CUSTOMER_IDS="):
            lines[i] = new_line
            updated = True
            break
    
    if not updated:
        lines.append(new_line)
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✓ Updated {env_path}")

if __name__ == "__main__":
    customers = discover_active_customers()
    
    if customers:
        print(f"\n=== DISCOVERED {len(customers)} ACTIVE CUSTOMERS ===")
        for cid, (name, hours) in sorted(customers.items()):
            print(f"{cid:>4}: {name:<40} ({hours:>5.1f}h)")
        
        # Ask user if they want to update .env
        response = input(f"\nUpdate .env with these {len(customers)} customer IDs? [y/N]: ")
        if response.lower() in ['y', 'yes']:
            update_env_file(customers.keys())
        else:
            print("Skipped .env update")
            print(f"Manual: REPORT_CUSTOMER_IDS={','.join(sorted(customers.keys()))}")
    else:
        print("❌ No active customers found")




