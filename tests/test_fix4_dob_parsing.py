import sys
import os
import unittest
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
import app as sewasetu_app


def parse_dob(dob_raw):
    """Helper mimicking the app's DOB parsing logic."""
    for fmt in sewasetu_app.DOB_FORMATS if hasattr(sewasetu_app, "DOB_FORMATS") else ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(dob_raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


class TestFix4DobParsing(unittest.TestCase):
    """
    Test Fix 4: Date of Birth Parsing Ambiguity.
    
    The legacy code in handle_submission used:
        for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
            try:
                dob = datetime.strptime(dob_raw, fmt).date()
                break
                
    This checked US format (%m/%d/%Y) BEFORE Indian format (%d/%m/%Y).
    For Indian dates like 04/05/1960 (4th May 1960):
    - The legacy code parses it as Month=4, Day=5 (5th April 1960).
    - This day/month inversion alters the citizen's actual age.
    - Around the 60-year pension threshold, this leads to wrongful eligibility rejection.
    - It also failed completely on HTML5 date inputs (YYYY-MM-DD) and hyphenated dates (DD-MM-YYYY).
    """

    def test_indian_date_format_prioritized_over_us_format(self):
        # 04/05/1960 is 4th May 1960 in India, NOT 5th April 1960
        dob_raw = "04/05/1960"
        parsed = parse_dob(dob_raw)
        self.assertIsNotNone(parsed, "DOB should be parsed successfully")
        self.assertEqual(parsed.day, 4, "Day should be 4 (Indian DD/MM/YYYY format)")
        self.assertEqual(parsed.month, 5, "Month should be 5 (May)")
        self.assertEqual(parsed.year, 1960)

    def test_iso_date_format_supported(self):
        # Standard HTML5 <input type="date"> sends YYYY-MM-DD
        dob_raw = "1960-05-04"
        parsed = parse_dob(dob_raw)
        self.assertIsNotNone(parsed, "ISO date format YYYY-MM-DD must be supported")
        self.assertEqual(parsed, date(1960, 5, 4))

    def test_hyphenated_indian_date_format_supported(self):
        # Common format DD-MM-YYYY
        dob_raw = "04-05-1960"
        parsed = parse_dob(dob_raw)
        self.assertIsNotNone(parsed, "Hyphenated Indian format DD-MM-YYYY must be supported")
        self.assertEqual(parsed, date(1960, 5, 4))


if __name__ == "__main__":
    unittest.main()
