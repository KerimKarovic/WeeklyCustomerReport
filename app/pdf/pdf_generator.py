
from typing import Dict, Optional
from pathlib import Path
from .weekly_report import WeeklyReportPDF
from app.services.resolve import CustomerPacket

def generate_customer_pdf(
    customer_packet: CustomerPacket,
    week_label: str,
    output_path: Optional[str] = None
) -> bytes:
    """Generate PDF for a single customer's timesheet data."""
    pdf = WeeklyReportPDF()
    pdf.add_page()
    
    pdf.add_customer_address(customer_packet["customer_name"])
    pdf.add_title_and_metadata(week_label, customer_packet)
    pdf.add_summary_section(customer_packet)
    pdf.add_details_section(customer_packet)
    
    if output_path:
        pdf.output(output_path)
        return Path(output_path).read_bytes()
    
    pdf_output = pdf.output(dest="S")
    if isinstance(pdf_output, str):
        return pdf_output.encode("latin1")
    return bytes(pdf_output)
