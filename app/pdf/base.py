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
        self.FONT_SMALL = 8
    
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
    
    def _format_hours(self, hours: float) -> str:
        """Format hours for display."""
        return f"{hours:.1f}h"



