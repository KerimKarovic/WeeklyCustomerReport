from pathlib import Path
from typing import List, Dict, Optional
from .base import BasePDF
from app.services.report_row import ReportRow
from app.services.resolve import CustomerPacket

class WeeklyReportPDF(BasePDF):
    """PDF generator for weekly timesheet reports matching the KIRATIK template."""

    # Stroke widths to match the first table design
    GRID_W: float = 0.25  # light grid width (mm)
    RULE_W: float = 0.45  # strong rule width (mm)
    ALIGN_NUDGE_L: float = -0.2  # Tiny nudge to align body text with header labels visually (mm)

    # Layout constants
    MARGIN_LEFT: float = 20  # Left margin (mm)
    MARGIN_RIGHT: float = 190  # Right margin (mm)
    CONTENT_WIDTH: float = 170  # Content width (mm)
    ADDRESS_X: float = 120  # Address block x position (mm)
    ADDRESS_WIDTH: float = 70  # Address block width (mm)
    HEADER_Y: float = 25  # Header line y position (mm)
    TITLE_Y: float = 70  # Title y position (mm)
    PAGE_HEIGHT: float = 297  # A4 page height (mm)
    FOOTER_SPACE: float = 40  # Space reserved for footer (mm)

    # Table constants
    SUMMARY_COL_WIDTHS: List[float] = [154, 16]  # Summary table column widths
    DETAILS_HEADERS: List[str] = ["Datum", "Verantwortlicher", "Projekt", "Ticket", "Beschreibung", "Zeit"]
    DETAILS_COL_WIDTHS: List[float] = [18, 28, 20, 35, 49, 16]  # Details table column widths

    # Text wrapping constants
    LINE_HEIGHT: float = 4  # Line height for text wrapping (mm)
    TEXT_PADDING: float = 2  # Text padding (mm)
    MAX_TEXT_LENGTH: int = 200  # Maximum text length before truncation

    # Color constants
    COLOR_GRAY_LIGHT: tuple = (200, 200, 200)  # Light gray for borders
    COLOR_GRAY_HEADER: tuple = (240, 240, 240)  # Gray for header background
    COLOR_BLACK: tuple = (0, 0, 0)  # Black
    COLOR_LOGO: tuple = (0, 120, 180)  # Logo color (blue)


    def __init__(self, *, logo_path: Optional[Path] = None):
        super().__init__()

        # Standardize cell margin so header and body text align
        self.c_margin = 2.0  # mm
        # Apply to FPDF cells if supported so header text uses the same margin
        try:
            if hasattr(self, "set_cell_margin"):
                self.set_cell_margin(self.c_margin)  # type: ignore
            elif hasattr(self, "c_margin"):
                # Fallback for older FPDF versions
                setattr(self, "c_margin", self.c_margin)
        except Exception:
            pass

        # Override logo path if provided
        if logo_path:
            self.logo_path = logo_path

        # Ensure header/footer are called automatically
        self.set_auto_page_break(auto=True, margin=30)  # Increase margin for footer

    def header(self):
        """Page header with logo and grey line."""
        if self.logo_path.exists():
            try:
                logo_width = 40
                logo_x = self.MARGIN_RIGHT - logo_width
                self.image(str(self.logo_path), x=logo_x, y=8, w=logo_width)
            except Exception:
                self._text_logo()
        else:
            self._text_logo()

        # Grey line
        self.set_draw_color(*self.COLOR_GRAY_LIGHT)
        self.line(self.MARGIN_LEFT, self.HEADER_Y, self.MARGIN_RIGHT, self.HEADER_Y)
        self.set_text_color(*self.COLOR_BLACK)
        self.set_draw_color(*self.COLOR_BLACK)

    def _text_logo(self):
        """Fallback text logo."""
        self.set_xy(150, 10)
        self.set_font(self.font_name, style="B", size=16)
        self.set_text_color(*self.COLOR_LOGO)
        self.cell(40, 10, "KIRATIK", align="R")

    def footer(self):
        """Page footer with contact and company info."""
        self.set_y(-30)
        self.set_font(self.font_name, size=8)
        self.set_text_color(128)

        contact_info = "📞 (+49) 7572 76 30 0    ✉ support@kiratik.de    🌐 https://www.kiratik.de    📄 USt.: DE229024302"
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

        self.cell(0, 4, f"Seite: {self.page_no()} of {{nb}}", align="R")
        self.set_text_color(0, 0, 0)

    def add_customer_address(self, customer_name: str):
        """Add customer address block on the right side."""
        # Customer address block on the right
        self.set_xy(self.ADDRESS_X, 35)
        self.set_font(self.font_name, style="B", size=9)

        # Wrap customer name if it's too long
        if self.get_string_width(customer_name) > self.ADDRESS_WIDTH:
            # Split long names into multiple lines
            words = customer_name.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self.get_string_width(test_line) <= self.ADDRESS_WIDTH:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            # Print each line of the customer name
            for i, line in enumerate(lines):
                self.set_xy(self.ADDRESS_X, 35 + i * 4)
                self.cell(self.ADDRESS_WIDTH, 4, line, align="L")

            # Adjust starting position for address based on number of name lines
            address_start_y = 35 + len(lines) * 4 + 2
        else:
            # Single line name
            self.cell(self.ADDRESS_WIDTH, 4, customer_name, align="L")
            address_start_y = 39

        # Placeholder address
        self.set_font(self.font_name, size=8)
        current_y = address_start_y
        self.set_xy(self.ADDRESS_X, current_y)
        self.cell(self.ADDRESS_WIDTH, 4, "Musterstraße 123", align="L")
        current_y += 4
        self.set_xy(self.ADDRESS_X, current_y)
        self.cell(self.ADDRESS_WIDTH, 4, "12345 Musterstadt", align="L")
        current_y += 4
        self.set_xy(self.ADDRESS_X, current_y)
        self.cell(self.ADDRESS_WIDTH, 4, "Deutschland", align="L")

    def add_title_and_metadata(self, week_label: str, customer_packet: CustomerPacket):
        """Add title and metadata with correct values."""
        from datetime import datetime

        # Main title
        self.set_xy(self.MARGIN_LEFT, self.TITLE_Y)
        self.set_font(self.font_name, style="B", size=14)
        self.cell(0, 10, "Arbeitszeitreport", align="L")
        self.ln(20)

        # Metadata with correct values
        y_pos = self.get_y()
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
        field_widths = [max(label_widths[i], value_widths[i]) + 2 for i in range(len(metadata_items))]

        # Calculate remaining space and distribute equally as gaps
        total_field_width = sum(field_widths)
        remaining_space = self.CONTENT_WIDTH - total_field_width
        gap_width = remaining_space / (len(metadata_items) - 1) if len(metadata_items) > 1 else 0

        # Labels row
        self.set_xy(self.MARGIN_LEFT, y_pos)
        self.set_font(self.font_name, style="B", size=8)
        x_pos = self.MARGIN_LEFT
        for i, (label, _) in enumerate(metadata_items):
            self.set_xy(x_pos, y_pos)
            self.cell(field_widths[i], 4, label, align="L")
            x_pos += field_widths[i] + gap_width

        # Values row
        self.set_xy(self.MARGIN_LEFT, y_pos + 4)
        self.set_font(self.font_name, size=8)
        x_pos = self.MARGIN_LEFT
        for i, (_, value) in enumerate(metadata_items):
            self.set_xy(x_pos, y_pos + 4)
            self.cell(field_widths[i], 4, value, align="L")
            x_pos += field_widths[i] + gap_width

        self.set_y(y_pos + 20)

    def _wrap_text(self, text: str, width: float) -> list:
        """Wrap text into lines based on available width.

        Args:
            text: Text to wrap
            width: Available width (mm)

        Returns:
            List of wrapped lines
        """
        if not text:
            return [""]

        text = str(text)
        max_width = width - self.TEXT_PADDING
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.get_string_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                if self.get_string_width(word) > max_width:
                    broken_parts = self._break_word_with_hyphen(word, max_width)
                    lines.extend(broken_parts[:-1])
                    current_line = broken_parts[-1]
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)
        return lines

    def _calculate_lines(self, text: str, width: float) -> int:
        """Calculate how many lines text will need when wrapped.

        Args:
            text: Text to calculate lines for
            width: Available width (mm)

        Returns:
            Number of lines needed
        """
        if not text:
            return 1

        text = str(text)
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH - 3] + "..."

        lines = self._wrap_text(text, width)
        return len(lines)

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

        # Wrap text using shared logic
        lines = self._wrap_text(str(text), max_text_width + self.TEXT_PADDING)

        # Calculate how many lines we can fit in the given height
        line_height = 4
        max_lines = max(1, int((height - 2) / line_height))

        # If we have more lines than fit, we'll return the overflow
        lines_to_draw = lines[:max_lines]

        # Calculate vertical centering offset
        total_text_height = len(lines_to_draw) * line_height
        vertical_offset = (height - total_text_height) / 2

        # Draw text lines with vertical centering
        for i, line in enumerate(lines_to_draw):
            if line:
                text_y = y + vertical_offset + i * line_height

                # Adjust horizontal positioning
                if align == "R":
                    self.set_xy(x + width - 4.0, text_y)
                    self.cell(4.0, line_height, line, align="R")
                else:
                    # Compensate for FPDF's internal cell margin so left edge aligns with header text
                    cm = getattr(self, "c_margin", 0)  # fpdf2 internal cell margin (mm)
                    nudge = getattr(self, "ALIGN_NUDGE_L", 0.0)
                    self.set_xy(x + pad_x - cm + nudge, text_y)
                    self.cell(max_text_width + cm, line_height, line, align="L")

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
        self.set_x(self.MARGIN_LEFT)
        self.cell(self.CONTENT_WIDTH, 8, "Übersicht", align="L")
        self.ln(10)

        # Calculate hours by classification
        hours_by_type = {}
        for row in customer_packet["rows"]:
            classification = row.classification
            hours_by_type[classification] = hours_by_type.get(classification, 0) + row.hours

        col_widths = self.SUMMARY_COL_WIDTHS

        # Header with black top border - match details table style
        self._set_header_style()
        self.set_x(self.MARGIN_LEFT)
        self.cell(col_widths[0], 8, "Aufgabe", border="T", fill=True, align="L")
        self.cell(col_widths[1], 8, "Zeit", border="T", fill=True, align="R")
        self.ln(8)

        # Add light gray borders for header sides/bottom
        self.set_draw_color(*self.COLOR_GRAY_LIGHT)
        self.set_line_width(self.GRID_W)
        self.set_xy(self.MARGIN_LEFT, self.get_y() - 8)
        self.cell(sum(col_widths), 8, "", border="LRB")
        self.ln(0)

        # Data rows with light gray borders
        self.set_font(self.font_name, size=self.FONT_MEDIUM)
        self.set_fill_color(255, 255, 255)

        for classification, hours in hours_by_type.items():
            service_line = f"{classification} - {customer_packet['customer_name']}"
            row_height = 8

            self.set_x(self.MARGIN_LEFT)
            self._multi_line_cell(col_widths[0], row_height, service_line, "1", "L", pad_x=self.c_margin)
            self._multi_line_cell(col_widths[1], row_height, self._format_hours(hours), "1", "R", pad_x=self.c_margin)
            self.ln(row_height)

        # Total row styling to match header: gray fill; only bottom border black
        total_hours = sum(hours_by_type.values())
        self._draw_footer_row(col_widths, "Total", self._format_hours(total_hours))

    def add_details_section(self, customer_packet: CustomerPacket):
        """Add Details section - centered."""
        # Check if we need a page break before starting details
        self._check_page_break(50)

        # Center the section title
        self.set_font(self.font_name, style="B", size=14)
        self.set_x(self.MARGIN_LEFT)
        self.cell(self.CONTENT_WIDTH, 8, "Details", align="L")
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
        needed_space = section_header_space + min_table_space

        self._check_page_break(needed_space)

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
        headers = self.DETAILS_HEADERS
        col_widths = self.DETAILS_COL_WIDTHS

        # Check if we have enough space for headers + at least one data row
        header_height = 8
        min_data_row_height = 12
        total_needed = header_height + min_data_row_height

        self._check_page_break(total_needed)

        self._add_table_headers(headers, col_widths)

        # Data rows with overflow handling
        self._set_data_row_style()

        for row in rows:
            # More conservative space checking
            min_row_height = 12

            if self._check_page_break(min_row_height):
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
                lines = self._calculate_lines(text, col_widths[i])
                max_lines = max(max_lines, lines)

            row_height = 6 * max_lines

            # Check if full row fits, if not, we'll handle overflow
            available_height = (self.PAGE_HEIGHT - self.FOOTER_SPACE) - self.get_y()

            if row_height <= available_height:
                # Row fits completely
                self._draw_table_row(texts, col_widths, row_height)
            else:
                # Row needs to be split across pages
                self._draw_table_row_with_overflow(texts, col_widths, available_height, headers)

        # Add total row with space check
        if self._check_page_break(12):
            self._add_table_headers(headers, col_widths)

        self._add_total_row(rows, col_widths)

    def _add_total_row(self, rows: List[ReportRow], col_widths: list):
        """Add total row at bottom of table."""
        total_hours = sum(row.hours for row in rows)
        self._draw_footer_row(col_widths, "Total", self._format_hours(total_hours))
        self.ln(5)  # Extra spacing after total row

    def _draw_table_row(self, texts: list, col_widths: list, row_height: float):
        """Draw a complete table row."""
        self._set_data_row_style()  # Ensure data row style is set (non-bold)
        self.set_x(self.MARGIN_LEFT)

        for i, text in enumerate(texts):
            # Match header alignment: Zeit (last column) right-aligned, others left-aligned
            align = "R" if i == len(texts) - 1 else "L"
            self._multi_line_cell(col_widths[i], row_height, text, "1", align, self.c_margin)

        self.ln(row_height)

    def _draw_table_row_with_overflow(self, texts: list, col_widths: list, available_height: float, headers: list):
        """Draw a table row that spans multiple pages."""
        self._set_data_row_style()  # Ensure data row style is set (non-bold)

        # Calculate how much we can fit on current page
        lines_that_fit = max(1, int((available_height - 4) / self.LINE_HEIGHT))
        partial_height = lines_that_fit * self.LINE_HEIGHT + 2

        # Draw partial row on current page
        self.set_x(self.MARGIN_LEFT)
        overflow_texts = []

        for i, text in enumerate(texts):
            align = "R" if i == len(texts) - 1 else "L"
            overflow = self._multi_line_cell(col_widths[i], partial_height, text, "1", align, pad_x=self.c_margin)
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
                    lines = self._calculate_lines(overflow_text, col_widths[i])
                    max_overflow_lines = max(max_overflow_lines, lines)

            overflow_height = 6 * max_overflow_lines
            self._draw_table_row(overflow_texts, col_widths, overflow_height)

    def _add_table_headers(self, headers, col_widths):
        """Helper to add table headers after page break.
        Matches the summary table: black top rule, light-gray left/right/bottom.
        """
        # Ensure we're positioned correctly after page break
        if self.get_y() < 55:
            self.set_y(55)

        HEADER_H = 8
        y0 = self.get_y()
        self.set_x(self.MARGIN_LEFT)

        # Header text with black top rule across full width
        self._set_header_style()
        for i, header in enumerate(headers):
            align = "R" if header == "Zeit" else "L"
            self.cell(col_widths[i], HEADER_H, header, border="T", fill=True, align=align)

        # Move down by header height
        self.ln(HEADER_H)

        # Add light-gray left/right/bottom around the header band
        self.set_draw_color(*self.COLOR_GRAY_LIGHT)
        self.set_line_width(self.GRID_W)
        self.set_xy(self.MARGIN_LEFT, y0)
        self.cell(sum(col_widths), HEADER_H, "", border="LRB")

        # Restore cursor just below the header band for the first data row
        self.set_y(y0 + HEADER_H)
        self.set_x(self.MARGIN_LEFT)

    def _set_header_style(self):
        """Set styling for table headers."""
        self.set_font(self.font_name, style="B", size=self.FONT_MEDIUM)
        self.set_fill_color(*self.COLOR_GRAY_HEADER)
        self.set_draw_color(*self.COLOR_BLACK)
        self.set_line_width(self.RULE_W)

    def _set_data_row_style(self):
        """Set styling for table data rows."""
        self.set_font(self.font_name, style="", size=self.FONT_SMALL)
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*self.COLOR_GRAY_LIGHT)
        self.set_line_width(self.GRID_W)

    def _check_page_break(self, needed_space: float, start_y: float = 55):
        """Check if we need a page break and add one if necessary.

        Args:
            needed_space: Space needed (mm)
            start_y: Y position to set after page break (default: 55)

        Returns:
            True if page break was added, False otherwise
        """
        if self.get_y() + needed_space > self.PAGE_HEIGHT - self.FOOTER_SPACE:
            self.add_page()
            self.set_y(start_y)
            return True
        return False

    def _draw_footer_row(self, col_widths: list, label: str, value: str):
        """Draw a footer row with gray fill and borders.

        Args:
            col_widths: List of column widths
            label: Text for the label column (left-aligned)
            value: Text for the value column (right-aligned)
        """
        self.set_font(self.font_name, style="B", size=self.FONT_MEDIUM)
        self.set_fill_color(*self.COLOR_GRAY_HEADER)

        y0 = self.get_y()
        self.set_x(self.MARGIN_LEFT)

        # Draw light-gray cells for all columns except the last
        self.set_draw_color(*self.COLOR_GRAY_LIGHT)
        FOOT_H = 8
        for width in col_widths[:-1]:
            self.cell(width, FOOT_H, "", border="LRT", fill=True)

        # Draw last column with light-gray
        self.cell(col_widths[-1], FOOT_H, "", border="LRT", fill=True)

        # Overlay text: label spans all columns except last, value in last column
        self.set_xy(self.MARGIN_LEFT - 0.5, y0 + 1)
        self.cell(sum(col_widths[:-1]) + 0.5, FOOT_H, label, align="L")
        self.set_xy(self.MARGIN_LEFT + sum(col_widths[:-1]), y0 + 1)
        self.cell(col_widths[-1], FOOT_H, value, align="R")

        # Black bottom border across full table width
        self.set_draw_color(*self.COLOR_BLACK)
        self.line(self.MARGIN_LEFT, y0 + FOOT_H, self.MARGIN_LEFT + sum(col_widths), y0 + FOOT_H)
        self.ln(10)

    def _format_hours(self, hours: float) -> str:
        """Format hours for display in PDF."""
        return f"{hours:.1f}h"
