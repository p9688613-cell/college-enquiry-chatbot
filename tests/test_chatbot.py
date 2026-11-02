"""
test_chatbot.py - Unit Test Suite for College Enquiry Chatbot
=============================================================
Tests all core functional requirements:
- Greetings and pleasantries
- Admission inquiries
- Course inquiries
- Fee structure inquiries
- College and library timings
- Examination and results
- Documents required
- Hostel & placements
- Fallback handling for unknown questions
- Input validation (empty text, whitespace)
- Paraphrased query robustness
- Database FAQ operations
"""

import os
import sys
import unittest

# Ensure the root project folder is in the Python module search path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from chatbot import CollegeChatbot
from database import init_db, get_all_faqs, add_faq, delete_faq, log_query, get_query_logs


class TestCollegeChatbot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize chatbot engine and database once for all tests."""
        init_db()
        intents_file = os.path.join(PROJECT_ROOT, 'data', 'intents.json')
        cls.bot = CollegeChatbot(intents_path=intents_file)

    # --------------------------------------------------------------------------
    # 1. GREETING & CONVERSATIONAL TESTS
    # --------------------------------------------------------------------------
    def test_greeting_messages(self):
        """Test standard greetings."""
        queries = ["hello", "Hi there", "Good morning", "hey"]
        for q in queries:
            result = self.bot.get_response(q)
            self.assertEqual(result['intent'], 'greeting', f"Failed for: {q}")
            self.assertFalse(result['is_fallback'])
            self.assertGreater(len(result['response']), 10)

    def test_goodbye_messages(self):
        """Test farewell phrases."""
        result = self.bot.get_response("bye see you later")
        self.assertEqual(result['intent'], 'goodbye')
        self.assertFalse(result['is_fallback'])

    def test_thanks_messages(self):
        """Test gratitude phrases."""
        result = self.bot.get_response("thank you for your help")
        self.assertEqual(result['intent'], 'thanks')
        self.assertFalse(result['is_fallback'])

    # --------------------------------------------------------------------------
    # 2. ADMISSION & ELIGIBILITY ENQUIRIES
    # --------------------------------------------------------------------------
    def test_admission_questions(self):
        """Test admission procedure inquiries."""
        result = self.bot.get_response("how to apply for admission in college")
        self.assertEqual(result['intent'], 'admissions')
        self.assertIn("admission", result['response'].lower())

    def test_eligibility_questions(self):
        """Test criteria and percentage requirements."""
        result = self.bot.get_response("what is the eligibility criteria for BCA")
        self.assertEqual(result['intent'], 'eligibility')
        self.assertIn("50%", result['response'])

    # --------------------------------------------------------------------------
    # 3. COURSE ENQUIRIES
    # --------------------------------------------------------------------------
    def test_course_enquiries(self):
        """Test courses offered queries."""
        result = self.bot.get_response("what courses are offered in your college")
        self.assertEqual(result['intent'], 'courses')
        self.assertIn("BCA", result['response'])
        self.assertIn("B.Sc", result['response'])

    # --------------------------------------------------------------------------
    # 4. FEE & SCHOLARSHIP ENQUIRIES
    # --------------------------------------------------------------------------
    def test_fee_enquiries(self):
        """Test fee structure questions."""
        result = self.bot.get_response("what is the fee structure for BCA course")
        self.assertEqual(result['intent'], 'fees')
        self.assertIn("45,000", result['response'])

    def test_scholarship_enquiries(self):
        """Test financial aid and scholarship queries."""
        result = self.bot.get_response("is any scholarship available for students")
        self.assertEqual(result['intent'], 'scholarships')
        self.assertIn("scholarship", result['response'].lower())

    # --------------------------------------------------------------------------
    # 5. TIMINGS & SCHEDULE
    # --------------------------------------------------------------------------
    def test_timing_questions(self):
        """Test working hours and lecture timing queries."""
        result = self.bot.get_response("what are the college opening timings")
        self.assertEqual(result['intent'], 'timings')
        self.assertIn("9:00 AM", result['response'])

    # --------------------------------------------------------------------------
    # 6. EXAMINATIONS & RESULTS
    # --------------------------------------------------------------------------
    def test_examination_questions(self):
        """Test exam timetable and hall ticket questions."""
        result = self.bot.get_response("when will semester exams be conducted")
        self.assertEqual(result['intent'], 'examinations')
        self.assertIn("exam", result['response'].lower())

    def test_results_questions(self):
        """Test exam result queries."""
        result = self.bot.get_response("how to check exam results")
        self.assertEqual(result['intent'], 'results')
        self.assertIn("result", result['response'].lower())

    # --------------------------------------------------------------------------
    # 7. DOCUMENTS, HOSTEL, & CONTACT
    # --------------------------------------------------------------------------
    def test_document_requirements(self):
        """Test admission document checklist."""
        result = self.bot.get_response("what documents are required for admission")
        self.assertEqual(result['intent'], 'documents')
        self.assertIn("10th", result['response'])
        self.assertIn("Transfer Certificate", result['response'])

    def test_hostel_facilities(self):
        """Test hostel queries."""
        result = self.bot.get_response("tell me about boys and girls hostel facilities")
        self.assertEqual(result['intent'], 'hostel')
        self.assertIn("hostel", result['response'].lower())

    def test_contact_details(self):
        """Test phone and address inquiries."""
        result = self.bot.get_response("what is the college contact number and address")
        self.assertEqual(result['intent'], 'contact')
        self.assertIn("98765 43210", result['response'])

    # --------------------------------------------------------------------------
    # 8. PARAPHRASING ROBUSTNESS (Same meaning, different words)
    # --------------------------------------------------------------------------
    def test_paraphrased_questions(self):
        """Verify that different phrasings of the same intent yield correct classification."""
        phrasings = [
            ("how much do I have to pay for BCA", "fees"),
            ("what is the fee of BCA", "fees"),
            ("annual charges for bca course", "fees"),
        ]
        for query, expected_intent in phrasings:
            res = self.bot.get_response(query)
            self.assertEqual(res['intent'], expected_intent, f"Failed for phrasing: {query}")

    # --------------------------------------------------------------------------
    # 9. UNKNOWN / OUT-OF-SCOPE QUESTIONS & FALLBACK
    # --------------------------------------------------------------------------
    def test_unknown_questions_trigger_fallback(self):
        """Ensure out-of-scope or random nonsense queries trigger graceful fallback."""
        nonsense_queries = [
            "who won the cricket world cup",
            "what is the recipe for chocolate cake",
            "asdfghjk qwerty xyz"
        ]
        for q in nonsense_queries:
            res = self.bot.get_response(q)
            self.assertTrue(res['is_fallback'], f"Did not fallback for: {q}")
            self.assertEqual(res['intent'], 'fallback')
            self.assertGreater(len(res['suggestions']), 0)

    # --------------------------------------------------------------------------
    # 10. EMPTY INPUT VALIDATION
    # --------------------------------------------------------------------------
    def test_empty_or_whitespace_input(self):
        """Test handling of empty, whitespace, and None input."""
        empty_inputs = ["", "   ", "\t\n"]
        for item in empty_inputs:
            res = self.bot.get_response(item)
            self.assertEqual(res['intent'], 'empty_input')
            self.assertTrue(res['is_fallback'])

    # --------------------------------------------------------------------------
    # 11. DATABASE OPERATIONS TEST
    # --------------------------------------------------------------------------
    def test_database_crud(self):
        """Test adding, retrieving, and deleting FAQs in SQLite."""
        test_cat = "TestCategory"
        test_q = "Is Wi-Fi available throughout campus?"
        test_a = "Yes, high-speed Wi-Fi is available across all departments and hostels."

        new_id = add_faq(test_cat, test_q, test_a, "wifi internet connectivity")
        self.assertIsNotNone(new_id)

        all_faqs = get_all_faqs()
        found = any(f['id'] == new_id for f in all_faqs)
        self.assertTrue(found)

        # Clean up
        deleted = delete_faq(new_id)
        self.assertTrue(deleted)

    def test_query_logging(self):
        """Test query logging for auditing and fallback tracking."""
        log_query("test query string", "testing", 0.99, is_fallback=0)
        logs = get_query_logs(limit=5)
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['user_query'], "test query string")


if __name__ == '__main__':
    unittest.main()

