from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
from typing import Dict, Any, Literal, Optional, TypedDict

# Allowed values (we'll translate to German in the email/PDF layer)
Classification = Literal["Service", "Support", "Kulanz"]
TaskStatus = Literal["done", "in_progress", "blocked", "unclear"]

@dataclass(slots=True)
class ReportRow:
    """
    Canonical shape for one line in the weekly report (no pricing).
    """
    worklog_id: int
    date: date
    task_id: int
    task_name: str
    task_url: str
    user: str
    hours: float
    classification: Classification
    task_status: TaskStatus
    customer_id: str
    customer_name: str
    project_id: str
    project_name: str
    description: str = ""  # Add description field for worklog text

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["date"] = self.date.isoformat()  # JSON-friendly
        return d

# --- helpers to keep data clean ---

def parse_date_from_iso_string(iso_date_string: str) -> date:
    """Parse ISO date string (YYYY-MM-DD) into a date object."""
    return date.fromisoformat(iso_date_string)

def normalize_work_classification(raw_classification: Optional[str]) -> Classification:
    """
    Normalize work classification from various input formats to standard values.
    
    Args:
        raw_classification: Raw classification string from Odoo or other sources
        
    Returns:
        Standardized Classification: "Service", "Support", or "Kulanz"
    """
    cleaned_input = (raw_classification or "").strip().lower()
    if cleaned_input == "service":
        return "Service"
    if cleaned_input == "support":
        return "Support"
    if cleaned_input in ("kulanz", "goodwill"):
        return "Kulanz"
    # Default to Support for unknown classifications
    return "Support"

def normalize_task_status_from_odoo(raw_status: Optional[str]) -> TaskStatus:
    """
    Convert Odoo task stage names (German) to standardized internal status.
    
    Based on your Odoo stages:
    - "in Bearbeitung" → "in_progress"
    - "Entwicklung" → "in_progress" 
    - "Erledigt" → "done"
    - "Blockiert" → "blocked"
    """
    cleaned_status = (raw_status or "").strip().lower()
    
    # Completed states (German)
    if cleaned_status in {"erledigt", "done", "fertig", "abgeschlossen", "closed"}:
        return "done"
    
    # Blocked/waiting states (German)
    if cleaned_status in {"blockiert", "blocked", "wartend", "waiting", "on hold"}:
        return "blocked"
    
    # Development/in progress (German)
    if cleaned_status in {"in bearbeitung", "entwicklung", "in progress", "bearbeitung"}:
        return "in_progress"
    
    # Unclear states
    if cleaned_status in {"unklar", "unclear"}:
        return "unclear"
    
    # Default to in_progress
    return "in_progress"

# Optional: a TypedDict if you prefer dict rows in some places
class ReportRowDict(TypedDict):
    worklog_id: int
    date: str
    task_id: int
    task_name: str
    task_url: str
    user: str
    hours: float
    classification: str
    task_status: str
    customer_id: str
    customer_name: str
    project_id: str
    project_name: str
