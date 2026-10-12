import sys
import os
import unittest
import werkzeug

if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3.0.0"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from app import app, get_db


class TestFix3IdorPrivacy(unittest.TestCase):
    """
    Test Fix 3: Insecure Direct Object Reference (IDOR) on Application Details.
    
    Vulnerability:
    In /application/<int:app_id> and /ack/<int:app_id>.pdf:
    Any logged-in citizen can view or download any other citizen's confidential
    records (bank account, IFSC, mobile, DOB, village) simply by guessing/incrementing
    the app_id parameter.
    
    Fix Requirement:
    A citizen can ONLY view or download their own application (matching session['portal_mobile']).
    If they attempt to access another citizen's record, they must be blocked (403 Forbidden).
    Staff administrators (session['admin'] is True) retain access to view all applications.
    """

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_citizen_cannot_view_another_citizens_application(self):
        # User is logged in as Citizen with different mobile number
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "9999999999"  # Does NOT match app_id=1's mobile

        response = self.client.get("/application/1")
        self.assertEqual(
            response.status_code,
            403,
            "Citizen should not be allowed to view another citizen's application details (IDOR)"
        )

    def test_unauthenticated_user_cannot_download_ack_pdf(self):
        # Direct access to acknowledgment PDF without login
        response = self.client.get("/ack/1.pdf")
        self.assertIn(
            response.status_code,
            (302, 401, 403),
            "Unauthenticated user should not be able to download arbitrary citizen acknowledgment PDFs"
        )

    def test_citizen_can_view_own_application(self):
        # Legitimate owner should have full access
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT mobile FROM applications WHERE id = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        self.assertIsNotNone(row, "Application id 1 should exist in seeded database")
        owner_mobile = row[0]

        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = owner_mobile

        response = self.client.get("/application/1")
        self.assertEqual(response.status_code, 200, "Owner should be able to view their own application")


if __name__ == "__main__":
    unittest.main()
