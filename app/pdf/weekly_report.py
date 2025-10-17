from typing import List
from .base import BasePDF
from app.services.report_row import ReportRow
from app.services.resolve import CustomerPacket

class WeeklyReportPDF(BasePDF):
    """PDF generator for weekly timesheet reports matching the KIRATIK template."""
    
    def __init__(self):
        super().__init__()
        

        # Ensure header/footer are called automatically
        self.set_auto_page_break(auto=True, margin=30)  # Increase margin for footer

    def header(self):
        """Page header with logo and grey line."""
        if self.logo_path.exists():
            try:
                logo_width = 40
                logo_x = 190 - logo_width
                self.image(str(self.logo_path), x=logo_x, y=8, w=logo_width)
            except Exception:
                self._text_logo()
        else:
            self._text_logo()
        
        # Grey line
        self.set_draw_color(200, 200, 200)
        self.line(20, 25, 190, 25)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
    
    def _text_logo(self):
        """Fallback text logo."""
        self.set_xy(150, 10)
        self.set_font(self.font_name, style="B", size=16)
        self.set_text_color(0, 120, 180)
        self.cell(40, 10, "KIRATIK", align="R")
    
    def footer(self):
        """Page footer with contact and company info."""
        self.set_y(-30)
        self.set_font(self.font_name, size=8)
        self.set_text_color(128)
        
        contact_info = "📞 (+49) 7572 76 30 0    ✉ support@kiratik.de    🌐 http://www.kiratik.de    📄 USt.: DE229024302"
        self.cell(0, 4, contact_info, align="C")
        self.ln(4)
        
        company_details = "KIRATIK GmbH, Sitz: Sigmaringen, Geschäftsführer: Sebastian Kiwitz, Amtsgericht Ulm HRB 560768, Steuer-Nr.: 81/060/08006"
        self.cell(0, 4, company_details, align="C")
        self.ln(4)
        
        banking_info = "Landesbank KSK Sigmaringen - IBAN DE31 6535 1050 0008 1955 15 - SWIFT-BIC SOLADES1SIG"
        self.cell(0, 4, banking_info, align="C")
        self.ln(4)
        
        banking_info2 = "Volksbank Bad Saulgau eG - IBAN DE46 6509 3020 0401 6760 05 - SWIFT-BIC GENODES1SLG"
        self.cell(0, 4, banking_info2, align="C")
        self.ln(6)
        
        self.cell(0, 4, f"Page: {self.page_no()} of {{nb}}", align="R")
        self.set_text_color(0, 0, 0)

    def add_customer_address(self, customer_name: str):
        """Add customer address block on the right side only."""
        # Customer address block on the right
        self.set_xy(120, 35)
        self.set_font(self.font_name, style="B", size=9)
        
        # Handle long German company names - split if needed
        if len(customer_name) > 35:
            words = customer_name.split()
            line1 = ""
            line2 = ""
            
            for word in words:
                if len(line1 + " " + word) <= 35:
                    line1 += (" " + word) if line1 else word
                else:
                    line2 += (" " + word) if line2 else word
            
            self.cell(0, 4, line1, align="L")
            self.ln(4)
            self.set_xy(120, 39)
            
            if line2:
                self.cell(0, 4, line2, align="L")
                self.ln(4)
                self.set_xy(120, 43)
        else:
            self.cell(0, 4, customer_name, align="L")
            self.ln(4)
            self.set_xy(120, 39)
        
        # Add customer address lines (placeholder - you'll need actual address data)
        self.set_font(self.font_name, size=8)
        self.cell(0, 4, "Musterstraße 123", align="L")
        self.ln(4)
        self.set_xy(120, self.get_y())
        self.cell(0, 4, "12345 Musterstadt", align="L")
        self.ln(4)
        self.set_xy(120, self.get_y())
        self.cell(0, 4, "Deutschland", align="L")

    def add_title_and_metadata(self, week_label: str, customer_packet: CustomerPacket):
        """Add title and metadata with correct values."""
        # Main title
        self.set_xy(20, 70)
        self.set_font(self.font_name, style="B", size=18)
        self.cell(0, 10, "Arbeitszeitreport", align="L")
        self.ln(20)
        
        # Metadata with correct values
        y_pos = self.get_y()
        
        # Generate proper values
        from datetime import datetime
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        # Define metadata with proper values
        metadata_items = [
            ("Rechnungsnummer:", f"AR-{datetime.now().strftime('%Y%m%d')}-{customer_packet['customer_id']}"),
            ("Beschreibung:", "Arbeitszeitreport"),
            ("Rechn.Datum:", current_date),
            ("Quelle:", "Timesheet"),
            ("Kunden-Nr.:", customer_packet["customer_id"]),
            ("Referenz:", week_label)
        ]
        
        # Calculate actual text widths
        self.set_font(self.font_name, style="B", size=8)
        label_widths = [self.get_string_width(label) for label, _ in metadata_items]
        
        self.set_font(self.font_name, size=8)
        value_widths = [self.get_string_width(value) for _, value in metadata_items]
        
        # Use maximum width needed for each field (label or value)
        field_widths = [max(label_widths[i], value_widths[i]) + 2 for i in range(len(metadata_items))]  # +2mm padding
        
        # Calculate remaining space and distribute equally as gaps
        total_field_width = sum(field_widths)
        remaining_space = 170 - total_field_width
        gap_width = remaining_space / (len(metadata_items) - 1) if len(metadata_items) > 1 else 0
        
        # Labels row
        self.set_xy(20, y_pos)
        self.set_font(self.font_name, style="B", size=8)
        x_pos = 20
        for i, (label, _) in enumerate(metadata_items):
            self.set_xy(x_pos, y_pos)
            self.cell(field_widths[i], 4, label, align="L")
            x_pos += field_widths[i] + gap_width
        
        # Values row
        self.set_xy(20, y_pos + 4)
        self.set_font(self.font_name, size=8)
        x_pos = 20
        for i, (_, value) in enumerate(metadata_items):
            self.set_xy(x_pos, y_pos + 4)
            self.cell(field_widths[i], 4, value, align="L")
            x_pos += field_widths[i] + gap_width
        
        self.set_y(y_pos + 20)

    def _calculate_lines(self, text: str, width: float) -> int:
        """Calculate how many lines text will need when wrapped."""
        if not text:
            return 1

        # Split text into words while preserving spaces
        import re
        words = re.split(r'(\s+)', str(text))
        words = [w for w in words if w]  # Keep all non-empty parts including spaces

        lines = 1
        current_line = ""

        for word in words:
            test_line = current_line + word
            if self.get_string_width(test_line) <= width - 2:  # 2mm padding
                current_line = test_line
            else:
                if current_line.strip():  # Only count as new line if current line has content
                    lines += 1
                current_line = word.strip()  # Start new line with word (no leading space)

        return lines

    def _multi_line_cell(self, width: float, height: float, text: str, border: str, align: str = "L", pad_x: float = 1.0):
        """Draw a cell with wrapped text using hyphenation for long words."""
        x, y = self.get_x(), self.get_y()

        # Draw border
        if border == "1":
            self.set_draw_color(200, 200, 200)  # Light gray
            self.rect(x, y, width, height)

        # Calculate maximum text width with padding
        max_text_width = width - (2 * pad_x)
        if max_text_width <= 0:
            return

        # Smart word wrapping with hyphenation
        words = str(text).split()
        lines = []
        current_line = ""
        
        for word in words:
            # Try to add word to current line
            test_line = current_line + (" " if current_line else "") + word
            
            if self.get_string_width(test_line) <= max_text_width:
                current_line = test_line
            else:
                # Word doesn't fit - check if we need to break it
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                
                # If single word is too long, break it with hyphen
                if self.get_string_width(word) > max_text_width:
                    broken_word = self._break_word_with_hyphen(word, max_text_width)
                    lines.extend(broken_word[:-1])  # Add all complete lines
                    current_line = broken_word[-1]  # Start new line with remainder
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        # Calculate how many lines we can fit in the given height
        line_height = 4
        max_lines = max(1, int((height - 2) / line_height))
        
        # If we have more lines than fit, we'll return the overflow
        lines_to_draw = lines[:max_lines]
        
        # Draw text lines with same positioning as headers (no vertical centering)
        for i, line in enumerate(lines_to_draw):
            if line:
                # For right-aligned text (times), always use the TOP of the cell regardless of line number
                if align == "R":
                    text_y = y + 2  # Always at top + padding, ignore line index for times
                else:
                    text_y = y + i * line_height + 2  # Normal line progression for other text
                
                # Adjust horizontal positioning to match headers better
                if align == "R":
                    # For right-aligned text (Zeit column), position near the right edge of the cell
                    self.set_xy(x + width - 4.0, text_y)
                    self.cell(4.0, line_height, line, align="R")
                elif align == "C":
                    self.set_xy(x + pad_x, text_y)
                    self.cell(max_text_width, line_height, line, align="C")
                else:
                    # For left-aligned text, move MORE to the left to reach border
                    self.set_xy(x + pad_x - 2.5, text_y)
                    self.cell(max_text_width + 2.5, line_height, line, align="L")

        # Move cursor to next position
        self.set_xy(x + width, y)
        
        # Return overflow lines for continuation on next page
        return lines[max_lines:] if len(lines) > max_lines else []

    def _break_word_with_hyphen(self, word: str, max_width: float) -> list:
        """Break a long word into multiple lines using hyphens."""
        if not word:
            return [""]
        
        lines = []
        remaining = word
        hyphen_width = self.get_string_width("-")
        
        while remaining:
            # Find the longest part that fits with a hyphen
            if self.get_string_width(remaining) <= max_width:
                # Remaining part fits completely
                lines.append(remaining)
                break
            
            # Binary search for the longest part that fits with hyphen
            left, right = 1, len(remaining)
            best_split = 1
            
            while left <= right:
                mid = (left + right) // 2
                test_part = remaining[:mid] + "-"
                
                if self.get_string_width(test_part) <= max_width:
                    best_split = mid
                    left = mid + 1
                else:
                    right = mid - 1
            
            # Ensure we don't split too aggressively (minimum 3 chars before hyphen)
            if best_split < 3 and len(remaining) > 3:
                best_split = 3
            
            # Add the part with hyphen
            lines.append(remaining[:best_split] + "-")
            remaining = remaining[best_split:]
        
        return lines if lines else [word]

    def add_summary_section(self, customer_packet: CustomerPacket):
        """Add Übersicht (summary) section with proper wrapping."""
        # Section title
        self.set_font(self.font_name, style="B", size=self.FONT_LARGE)
        self.set_x(20)
        self.cell(170, 8, "Übersicht", align="L")
        self.ln(10)
        
        # Calculate hours by classification
        hours_by_type = {}
        for row in customer_packet["rows"]:
            classification = row.classification
            hours_by_type[classification] = hours_by_type.get(classification, 0) + row.hours
        
        # Table widths - MATCH the details table exactly
        col_widths = [154, 16]  # 170 - 16 = 154 for Aufgabe, 16 for Zeit
        
        # Header with black top border - match details table style
        self.set_font(self.font_name, style="B", size=self.FONT_MEDIUM)
        self.set_fill_color(240, 240, 240)
        self.set_draw_color(0, 0, 0)  # Black for header top
        
        self.set_x(20)
        self.cell(col_widths[0], 8, "Aufgabe", border="T", fill=True, align="L")
        self.cell(col_widths[1], 8, "Zeit", border="T", fill=True, align="R")
        self.ln(8)  # Move down by header height
        
        # Add light gray borders for header sides/bottom
        self.set_draw_color(200, 200, 200)
        self.set_xy(20, self.get_y() - 8)
        self.cell(sum(col_widths), 8, "", border="LRB")
        self.ln(0)  # Stay at current position after drawing borders
        
        # Data rows with light gray borders
        self.set_font(self.font_name, size=self.FONT_MEDIUM)
        self.set_fill_color(255, 255, 255)
        
        for classification, hours in hours_by_type.items():
            service_line = f"{classification} - {customer_packet['customer_name']}"

            # Calculate row height based on text
            row_height = 8  # Fixed row height for summary table

            self.set_x(20)
            self._multi_line_cell(col_widths[0], row_height, service_line, "1", "L", pad_x=2.0)
            self._multi_line_cell(col_widths[1], row_height, self._format_hours(hours), "1", "R", pad_x=2.0)
            self.ln(row_height)
        
        # Total row styling to match header: gray fill; only bottom border black
        total_hours = sum(hours_by_type.values())
        self.set_font(self.font_name, style="B", size=self.FONT_MEDIUM)
        self.set_fill_color(240, 240, 240)
        y0 = self.get_y()
        self.set_x(20)
        # Light-gray sides + top (draw empty cells first)
        self.set_draw_color(200, 200, 200)
        self.set_x(20)
        FOOT_H = 8
        self.cell(col_widths[0], FOOT_H, "", border="LRT", fill=True)
        self.cell(col_widths[1], FOOT_H, "", border="LRT", fill=True)
        # Overlay text with padding to match data rows
        self.set_xy(20 - 0.5, y0 + 1)  # Move Total text LEFT by only -0.5mm
        self.cell(sum(col_widths[:-1]) + 0.5, FOOT_H, "Total", align="L")
        self.set_xy(20 + sum(col_widths[:-1]), y0 + 1)
        self.cell(col_widths[-1], FOOT_H, self._format_hours(total_hours), align="R")
        # Black bottom border across full table width
        self.set_draw_color(0, 0, 0)
        self.line(20, y0 + FOOT_H, 20 + sum(col_widths), y0 + FOOT_H)
        self.ln(10)

    def add_details_section(self, customer_packet: CustomerPacket):
        """Add Details section - centered."""
        # Check if we need a page break before starting details
        if self.get_y() > 180:  # If we're too far down the page
            self.add_page()
            self.set_y(55)  # Start below header line
        
        # Center the section title
        self.set_font(self.font_name, style="B", size=14)
        self.set_x(20)
        self.cell(170, 8, "Details", align="L")  # Left align but with proper margins
        self.ln(10)
        
        # Group by classification
        rows_by_classification = {}
        for row in customer_packet["rows"]:
            classification = row.classification
            if classification not in rows_by_classification:
                rows_by_classification[classification] = []
            rows_by_classification[classification].append(row)
        
        for classification, rows in rows_by_classification.items():
            self._add_classification_section(classification, customer_packet["customer_name"], rows)

    def _add_classification_section(self, classification: str, customer_name: str, rows: List[ReportRow]):
        """Add a section for one classification type with better page break handling."""
        # More conservative space checking
        section_header_space = 25  # Space needed for section header + project element
        min_table_space = 40      # Minimum space for table start (header + one row)
        footer_space = 40         # Space reserved for footer
        
        needed_space = section_header_space + min_table_space
        
        if self.get_y() + needed_space > 297 - footer_space:
            self.add_page()
            self.set_y(55)  # Start below header line
        
        # Section header
        self.set_font(self.font_name, style="B", size=10)
        self.set_x(20)
        
        available_width = 170
        header_text = f"{classification} - {customer_name}"
        
        # Truncate text to fit if needed
        while self.get_string_width(header_text) > available_width and len(header_text) > 10:
            header_text = header_text[:-4] + "..."
        
        self.cell(available_width, 8, header_text, align="L")
        self.ln(8)
        
        # Project element
        if rows and rows[0].project_name:
            self.set_font(self.font_name, style="B", size=9)
            self.set_x(20)
            project_text = f"Auftragselement: {rows[0].project_name}"
            
            while self.get_string_width(project_text) > available_width and len(project_text) > 15:
                project_text = project_text[:-4] + "..."
            
            self.cell(available_width, 6, project_text, align="L")
            self.ln(8)
        
        # Details table
        self._add_timesheet_table(rows)
        self.ln(5)

    def _add_timesheet_table(self, rows: List[ReportRow]):
        """Add detailed timesheet table with proper page flow management."""
        headers = ["Datum", "Verantwortlicher", "Projekt", "Ticket", "Beschreibung", "Zeit"]
        # Further optimized widths: more space for Projekt column
        col_widths = [18, 22, 22, 42, 50, 16]  # Total: 170mm
        # Changes: Projekt 18→22 (+4mm), reduced others slightly
        
        # Check if we have enough space for headers + at least one data row
        header_height = 8
        min_data_row_height = 12
        footer_space = 40  # Increased footer space
        total_needed = header_height + min_data_row_height
        
        if self.get_y() + total_needed > 297 - footer_space:
            self.add_page()
        
        self._add_table_headers(headers, col_widths)
        
        # Data rows with overflow handling
        self.set_font(self.font_name, size=self.FONT_SMALL)
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(200, 200, 200)
        
        for row in rows:
            # More conservative space checking
            min_row_height = 12  # Increased minimum
            
            if self.get_y() + min_row_height > 297 - footer_space:
                self.add_page()
                self._add_table_headers(headers, col_widths)
            
            # Prepare row data
            texts = [
                row.date.strftime("%d.%m.%Y"),
                row.user,
                row.project_name,
                row.task_name,
                row.description if row.description else "",
                self._format_hours(row.hours)
            ]
            
            # Calculate initial row height
            max_lines = 1
            for i, text in enumerate(texts):
                lines = self._calculate_lines_smart(text, col_widths[i])
                max_lines = max(max_lines, lines)
            
            row_height = 6 * max_lines
            
            # Check if full row fits, if not, we'll handle overflow
            available_height = (297 - footer_space) - self.get_y()
            
            if row_height <= available_height:
                # Row fits completely
                self._draw_table_row(texts, col_widths, row_height)
            else:
                # Row needs to be split across pages
                self._draw_table_row_with_overflow(texts, col_widths, available_height, headers)
        
        # Add total row with space check
        if self.get_y() + 12 > 297 - footer_space:
            self.add_page()
            self._add_table_headers(headers, col_widths)
        
        self._add_total_row(rows, col_widths)

    def _add_total_row(self, rows: List[ReportRow], col_widths: list):
        """Add total row at bottom of table."""
        total_hours = sum(row.hours for row in rows)
        self.set_font(self.font_name, style="B", size=self.FONT_MEDIUM)
        self.set_fill_color(240, 240, 240)
        
        y0 = self.get_y()
        self.set_x(20)
        
        self.set_draw_color(200, 200, 200)
        FOOT_H = 8
        self.cell(sum(col_widths[:-1]), FOOT_H, "", border="LRT", fill=True)
        self.cell(col_widths[-1], FOOT_H, "", border="LRT", fill=True)
        
        self.set_xy(20, y0 + 1)
        self.cell(sum(col_widths[:-1]), FOOT_H, "Total", align="L")
        self.set_xy(20 + sum(col_widths[:-1]), y0 + 1)
        self.cell(col_widths[-1], FOOT_H, self._format_hours(total_hours), align="R")
        
        self.set_draw_color(0, 0, 0)
        self.line(20, y0 + FOOT_H, 20 + sum(col_widths), y0 + FOOT_H)
        self.ln(15)  # Add space after table

    def _draw_table_row(self, texts: list, col_widths: list, row_height: float):
        """Draw a complete table row."""
        self.set_x(20)
        
        for i, text in enumerate(texts):
            # Match header alignment: Zeit (last column) right-aligned, others left-aligned
            align = "R" if i == len(texts) - 1 else "L"
            # Increase padding further to prevent text touching borders
            pad_x = 2.0  # Increased from 1.5mm to 2.0mm
            self._multi_line_cell(col_widths[i], row_height, text, "1", align, pad_x)
        
        self.ln(row_height)  # Add space after table

    def _draw_table_row_with_overflow(self, texts: list, col_widths: list, available_height: float, headers: list):
        """Draw a table row that spans multiple pages."""
        # Calculate how much we can fit on current page
        line_height = 4
        lines_that_fit = max(1, int((available_height - 4) / line_height))  # -4 for padding
        partial_height = lines_that_fit * line_height + 2  # +2 for padding
        
        # Draw partial row on current page
        self.set_x(20)
        overflow_texts = []
        
        for i, text in enumerate(texts):
            align = "R" if i == len(texts) - 1 else "L"
            overflow = self._multi_line_cell(col_widths[i], partial_height, text, "1", align, pad_x=1.0)
            overflow_texts.append(" ".join(overflow) if overflow else "")
        
        self.ln(partial_height)
        
        # Continue on next page if there's overflow
        if any(overflow_texts):
            self.add_page()
            self._add_table_headers(headers, col_widths)
            
            # Calculate height needed for overflow
            max_overflow_lines = 1
            for i, overflow_text in enumerate(overflow_texts):
                if overflow_text:
                    lines = self._calculate_lines_smart(overflow_text, col_widths[i])
                    max_overflow_lines = max(max_overflow_lines, lines)
            
            overflow_height = 6 * max_overflow_lines
            self._draw_table_row(overflow_texts, col_widths, overflow_height)

    def _calculate_lines_smart(self, text: str, width: float) -> int:
        """Calculate lines needed with smart word breaking."""
        if not text:
            return 1
        
        text = str(text)
        max_width = width - 2  # Account for padding
        
        words = text.split()
        lines = 1
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            
            if self.get_string_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines += 1
                
                # Check if word needs breaking
                if self.get_string_width(word) > max_width:
                    broken_parts = self._break_word_with_hyphen(word, max_width)
                    lines += len(broken_parts) - 1  # -1 because we already counted one line
                    current_line = broken_parts[-1]
                else:
                    current_line = word
        
        return lines

    def _add_table_headers(self, headers, col_widths):
        """Helper to add table headers after page break."""
        # Ensure we're positioned correctly after page break
        if self.get_y() < 55:
            self.set_y(55)  # Start below header line
        
        self.set_font(self.font_name, style="B", size=self.FONT_MEDIUM)
        self.set_fill_color(240, 240, 240)
        
        HEADER_H = 8
        self.set_draw_color(200, 200, 200)
        self.set_x(20)
        
        # Draw header cells with proper alignment
        for i, header in enumerate(headers):
            align = "R" if header == "Zeit" else "L"
            self.cell(col_widths[i], HEADER_H, header, border="1", fill=True, align=align)
        
        self.ln(HEADER_H)
        self.set_font(self.font_name, size=self.FONT_SMALL)
        self.set_fill_color(255, 255, 255)

    def _calculate_lines_limited(self, text: str, width: float) -> int:
        """Calculate lines needed with reasonable limits."""
        if not text:
            return 1
        
        # Limit text length to prevent excessive wrapping
        text = str(text)
        if len(text) > 200:  # Truncate very long text
            text = text[:197] + "..."
        
        words = text.split()
        lines = 1
        current_line = ""
        max_width = width - 2  # Account for padding

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.get_string_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines += 1
                current_line = word
                
            # Cap at 4 lines maximum
            if lines >= 4:
                break

        return min(lines, 4)

    def _format_hours(self, hours: float) -> str:
        """Format hours for display in PDF."""
        return f"{hours:.1f}h"
