import sys
import os
import unittest
import werkzeug

if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3.0.0"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from app import app


class TestFix2AccessControl(unittest.TestCase):
    """
    Test Fix 2: Broken Access Control on Pension Approval & Rejection.
    
    Vulnerability:
    In app.py, admin_approve and admin_reject check:
        if not session.get("logged_in"):
            abort(403)
            
    When a citizen logs in via /status, the session has:
        session["logged_in"] = True
        session["portal_mobile"] = mobile
        
    Because it only checked session.get("logged_in") instead of session.get("admin"),
    a regular citizen could issue POST requests to approve or reject any application
    without staff authority.
    
    Fix requirement:
    Only authenticated admin staff (session.get("admin") is True) must be allowed
    to execute admin actions. Non-admin users must be rejected with 403 Forbidden.
    """

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_citizen_cannot_approve_application(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "9876543210"
            # Note: sess["admin"] is NOT set, simulating a logged-in citizen

        response = self.client.post("/admin/approve/1")
        self.assertEqual(
            response.status_code, 
            403, 
            "A citizen user must not be authorized to approve applications (expected 403 Forbidden)"
        )

    def test_citizen_cannot_reject_application(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "9876543210"
            # Note: sess["admin"] is NOT set

        response = self.client.post("/admin/reject/1")
        self.assertEqual(
            response.status_code, 
            403, 
            "A citizen user must not be authorized to reject applications (expected 403 Forbidden)"
        )

    def test_unauthenticated_user_cannot_approve_or_reject(self):
        resp_approve = self.client.post("/admin/approve/1")
        self.assertEqual(resp_approve.status_code, 403)

        resp_reject = self.client.post("/admin/reject/1")
        self.assertEqual(resp_reject.status_code, 403)


if __name__ == "__main__":
    unittest.main()
