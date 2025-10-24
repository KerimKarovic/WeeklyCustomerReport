"""
Report logging service for tracking sent customer reports.
"""
import sqlite3
import json
from pathlib import Path
from typing import List

class ReportLog:
    """Track sent reports to prevent duplicates."""
    
    def __init__(self, db_path: str = "data/report_log.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS report_log (
                    customer_id TEXT,
                    week_label TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    recipients TEXT,
                    filename TEXT,
                    PRIMARY KEY (customer_id, week_label)
                )
            """)
    
    def was_sent(self, customer_id: str, week_label: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT 1 FROM report_log WHERE customer_id = ? AND week_label = ?",
                (customer_id, week_label)
            ).fetchone()
        return result is not None
    
    def mark_sent(self, customer_id: str, week_label: str, recipients: List[str], filename: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO report_log 
                (customer_id, week_label, recipients, filename)
                VALUES (?, ?, ?, ?)
            """, (customer_id, week_label, json.dumps(recipients), filename))
