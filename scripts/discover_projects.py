#!/usr/bin/env python3
"""
Discover active projects from Odoo based on timesheet activity.
Updates .env with REPORT_PROJECT_IDS for use in main.py.

Usage:
  python scripts/discover_projects.py
  python scripts/discover_projects.py --days-back 90 --min-hours 1.0
"""
import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.odoo import OdooClient


def discover_active_projects(days_back=90, min_hours=1.0):
    """Find projects with timesheet activity in the last N days."""
    cli = OdooClient()
    
    if cli.use_stub:
        print("❌ Cannot discover projects in stub mode")
        return {}
    
    end = date.today()
    start = end - timedelta(days=days_back)
    
    print(f"Discovering projects from {start} to {end} (min {min_hours}h)...")
    
    uid, models = cli._rpc_authenticate()
    
    # Get all timesheets in period
    domain = [
        ["date", ">=", start.isoformat()],
        ["date", "<=", end.isoformat()]
    ]
    
    timesheets = models.execute_kw(
        cli.db, uid, cli.password,
        "account.analytic.line", "search_read",
        [domain], {"fields": ["project_id", "unit_amount"]}
    )
    
    # Count hours per project
    project_hours = {}  # Dict[str, float]
    project_names = {}
    
    for ts in timesheets:
        project_info = ts.get("project_id")
        if project_info:  # Skip entries without project
            project_id = str(project_info[0])
            project_name = str(project_info[1])
            hours = float(ts.get("unit_amount", 0))
            
            project_hours[project_id] = project_hours.get(project_id, 0.0) + hours
            project_names[project_id] = project_name
    
    # Filter by minimum hours
    active_projects = {
        pid: (project_names[pid], hours) 
        for pid, hours in project_hours.items() 
        if hours >= min_hours
    }
    
    return active_projects


def update_env_file(project_ids):
    """Update .env file with discovered project IDs."""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"❌ {env_path} not found")
        return
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update REPORT_PROJECT_IDS line
    project_ids_str = ",".join(sorted(project_ids))
    new_line = f"REPORT_PROJECT_IDS={project_ids_str}\n"
    
    # Find and replace the line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("REPORT_PROJECT_IDS="):
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
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Discover active projects from Odoo")
    parser.add_argument("--days-back", type=int, default=90, help="Days back to search (default: 90)")
    parser.add_argument("--min-hours", type=float, default=1.0, help="Minimum hours threshold (default: 1.0)")
    args = parser.parse_args()
    
    projects = discover_active_projects(days_back=args.days_back, min_hours=args.min_hours)
    
    if projects:
        print(f"\n=== DISCOVERED {len(projects)} ACTIVE PROJECTS ===")
        for pid, (name, hours) in sorted(projects.items()):
            print(f"{pid:>4}: {name:<40} ({hours:>5.1f}h)")
        
        # Ask user if they want to update .env
        response = input(f"\nUpdate .env with these {len(projects)} project IDs? [y/N]: ")
        if response.lower() in ['y', 'yes']:
            update_env_file(projects.keys())
        else:
            print("Skipped .env update")
            print(f"Manual: REPORT_PROJECT_IDS={','.join(sorted(projects.keys()))}")
    else:
        print("❌ No active projects found")

