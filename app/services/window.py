from __future__ import annotations
from datetime import date, timedelta
from typing import Tuple, Optional

def calculate_reporting_week_with_offset(offset_days: int = 14, reference_date: Optional[date] = None) -> Tuple[date, date, str]:
    """
    Calculate the Monday–Sunday reporting window that is offset_days in the past.

    Example:
        If reference_date = 2025-09-10 and offset_days = 14,
        anchor_date = 2025-08-27 (Wed)
        week_start  = 2025-08-25 (Mon)
        week_end    = 2025-08-31 (Sun)
        week_label  = "KW 35 (2025-08-25 – 2025-08-31)"

    Args:
        offset_days: How many days back to anchor the week (default 14 = two-week lag)
        reference_date: Optional fixed date for testing. If None, uses date.today()

    Returns:d
        Tuple of (week_start_date, week_end_date, german_week_label)
    """
    if reference_date is None:
        reference_date = date.today()

    # Calculate anchor date by going back the specified offset
    anchor_date = reference_date - timedelta(days=offset_days)

    # Find Monday of that week (weekday(): Mon=0..Sun=6)
    week_start_date = anchor_date - timedelta(days=anchor_date.weekday())

    # Find Sunday of that week
    week_end_date = week_start_date + timedelta(days=6)

    # Create German ISO week label "KW {week} (YYYY-MM-DD – YYYY-MM-DD)"
    iso_calendar = week_start_date.isocalendar()
    german_week_label = f"KW {iso_calendar.week} ({week_start_date.isoformat()} – {week_end_date.isoformat()})"

    return week_start_date, week_end_date, german_week_label

