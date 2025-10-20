"""
File cleanup utilities for managing old PDF reports.
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

def cleanup_old_pdfs(output_dir: Path, days: Optional[int] = None) -> int:
    """
    Delete PDF files older than specified days from output directory.
    
    Args:
        output_dir: Directory containing PDF files
        days: Number of days to retain (default from env PDF_RETENTION_DAYS or 30)
    
    Returns:
        Number of files deleted
    """
    if days is None:
        days = int(os.getenv("PDF_RETENTION_DAYS", "30"))
    
    if not output_dir.exists():
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for pdf_file in output_dir.glob("*.pdf"):
        try:
            file_mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
            if file_mtime < cutoff_time:
                pdf_file.unlink()
                deleted_count += 1
        except (OSError, ValueError):
            # Skip files we can't process
            continue
    
    return deleted_count