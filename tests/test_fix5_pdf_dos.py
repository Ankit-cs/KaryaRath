import sys
import os
import time
import unittest
import werkzeug

if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3.0.0"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from app import app, get_db, generate_acknowledgment


class TestFix5PdfPerformance(unittest.TestCase):
    """
    Test Fix 5: PDF Generation Denial of Service & Worker Starvation.
    
    The legacy generate_acknowledgment function contains:
        for i in range(0, 2000):
            x = 10 + (i % 190)
            pdf.line(x, 282, x + 0.5, 282)
            pdf.line(x, 12, x + 0.5, 12)
            
    This draws 4,000 micro line segments on every PDF generation, taking over 0.6 seconds
    per document. Under the month-end traffic spikes simulated by the assessor probe,
    all worker threads saturate and Nginx returns 504 timeouts.
    
    Fix Requirement:
    Replace the 2000-iteration loop with clean, instantaneous header/footer rules (< 0.15s).
    """

    def test_pdf_generation_fast_and_efficient(self):
        conn = get_db()
        cur = conn.cursor()
        
        t0 = time.time()
        pdf_bytes = generate_acknowledgment(cur, 1)
        elapsed = time.time() - t0
        
        cur.close()
        conn.close()

        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Must output a valid PDF document")
        
        # A single page PDF without the 2,000-line loop generates in under 0.15 seconds.
        # With the loop, it takes 0.65 - 1.2+ seconds, blocking workers.
        self.assertLess(
            elapsed, 
            0.15, 
            f"PDF generation took {elapsed:.3f}s - 2000-line drawing loop causes worker starvation"
        )


if __name__ == "__main__":
    unittest.main()
