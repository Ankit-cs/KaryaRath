import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from app import sanitize


class TestFix1NameIntegrity(unittest.TestCase):
    """
    Test Fix 1: Indian-language name sanitization and data integrity.
    
    The legacy sanitize() function used:
        def sanitize(value, maxlen=20):
            encoded = value.encode("utf-8")[:maxlen]
            return encoded.decode("utf-8", errors="ignore")
            
    In handle_submission():
        name = sanitize(data.get("applicant_name", ""))
    
    Because maxlen defaulted to 20 bytes:
    1. For Indic scripts (Devanagari, Assamese, Bengali, etc.), 1 character = 3 bytes.
       A name like 'रामेश्वर प्रसाद शर्मा' was brutally truncated to 6 characters ('रामेश्व').
    2. Long Indian names like 'Surendranath Chattopadhyay' were truncated to 20 letters.
    
    The schema defines:
        applicant_name VARCHAR(100)
    
    The sanitization must preserve names up to the full database field length (100 characters),
    and must NOT truncate multi-byte UTF-8 sequences midway.
    """

    def test_default_sanitize_preserves_hindi_name(self):
        # Hindi name (54 UTF-8 bytes, 20 characters)
        hindi_name = "रामेश्वर प्रसाद शर्मा"
        sanitized = sanitize(hindi_name)
        self.assertEqual(sanitized, hindi_name, "Hindi name must be preserved faithfully")

    def test_default_sanitize_preserves_assamese_name(self):
        # Assamese name (39 UTF-8 bytes, 13 characters)
        assamese_name = "ৰাজেন বৰবৰুৱা"
        sanitized = sanitize(assamese_name)
        self.assertEqual(sanitized, assamese_name, "Assamese name must be preserved faithfully")

    def test_default_sanitize_preserves_long_english_name(self):
        long_name = "Surendranath Chattopadhyay"
        sanitized = sanitize(long_name)
        self.assertEqual(sanitized, long_name, "Names up to 100 characters must not be cut at 20 bytes")


if __name__ == "__main__":
    unittest.main()
