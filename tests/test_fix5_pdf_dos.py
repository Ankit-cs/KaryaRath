import sys
import os
import unittest
import werkzeug

if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3.0.0"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from app import app, get_db, generate_acknowledgment


class TestFix5PdfPerformance(unittest.TestCase):
    """
    Test Fix 5: PDF Generation Denial of Service & Worker Starvation.
    
    The legacy generate_acknowledgment function contained:
        for i in range(0, 2000):
            x = 10 + (i % 190)
            pdf.line(x, 282, x + 0.5, 282)
            pdf.line(x, 12, x + 0.5, 12)
            
    This drew 4,000 redundant line-drawing operations per PDF document.
    Under the month-end traffic spikes simulated by the assessor probe,
    this synchronous vector computation locks worker threads and exhausts CPU,
    causing 504 Gateway Timeouts.
    
    Fix Requirement:
    Replace the 2000-iteration micro-line loop with clean, efficient borders
    (e.g., top and bottom margin rules with minimal vector operations).
    """

    def test_pdf_does_not_contain_excessive_drawing_loops(self):
        conn = get_db()
        cur = conn.cursor()
        
        pdf_bytes = generate_acknowledgment(cur, 1)
        
        cur.close()
        conn.close()

        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Must output a valid PDF document")
        
        # The legacy loop injected 4,000 line drawing commands ("l" in PDF stream).
        # Clean letterhead borders should contain only a handful of line operations (< 50).
        line_draw_count = pdf_bytes.count(b" l\n")
        self.assertLess(
            line_draw_count, 
            50, 
            f"PDF stream contains {line_draw_count} drawing operations - 2,000-line loop must be removed"
        )


if __name__ == "__main__":
    unittest.main()
