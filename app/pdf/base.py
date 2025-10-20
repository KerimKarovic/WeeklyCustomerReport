from fpdf import FPDF
from pathlib import Path

class BasePDF(FPDF):
    """Base PDF class with common setup and utilities."""
    
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages()
        
        # Paths and fonts
        self.font_path = Path(__file__).parent.parent.parent / "fonts"
        self.logo_path = self.font_path / "kiratik_logo.png"
        self._setup_fonts()
        
        # Font sizes
        self.FONT_LARGE = 14
        self.FONT_MEDIUM = 10
        self.FONT_SMALL = 10
    
    def _setup_fonts(self):
        """Setup Calibri font configuration."""
        self.font_name = "Calibri"
        
        try:
            calibri_path = self.font_path / "calibri.ttf"
            calibri_bold_path = self.font_path / "calibrib.ttf"
            
            if calibri_path.exists() and calibri_bold_path.exists():
                self.add_font("Calibri", fname=str(calibri_path))
                self.add_font("Calibri", style="B", fname=str(calibri_bold_path))
                print("✓ Using Calibri fonts")
            else:
                print("⚠️  Calibri fonts not found. Using Arial fallback.")
                self.font_name = "Arial"
        except Exception as e:
            print(f"⚠️  Calibri font loading failed: {e}. Using Arial fallback.")
            self.font_name = "Arial"
    
    def _try_set_font(self, font_family: str, size: int = 10) -> str:
        """Try to set a font family, falling back to Calibri if not available."""
        try:
            # Try to add and set the requested font
            font_path = self.font_path / f"{font_family.lower()}.ttf"
            if font_path.exists():
                self.add_font(font_family, fname=str(font_path))
                self.set_font(font_family, size=size)
                return font_family
            else:
                # Font file not found, use default
                self.set_font(self.font_name, size=size)
                return self.font_name
        except Exception:
            # If anything fails, fall back to default font
            self.set_font(self.font_name, size=size)
            return self.font_name

    def _format_hours(self, hours: float) -> str:
        """Format hours for display."""
        return f"{hours:.1f}h"



