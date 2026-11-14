"""
BUSGO System Verification & Test Suite
Covers all functional requirements and test cases specified in SRS Section 12:
- TC-01: User Registration
- TC-02: User Login
- TC-03: Bus Search
- TC-04: Invalid Search Input
- TC-05: Price Comparison
- TC-06: RAG Question
- TC-07: Unsupported RAG Question
- TC-08: AI Agent Tool Calling
- TC-09: Seat Selection
- TC-10: Booking History
- TC-11: Claude Fallback Reliability
- TC-12: Booking Confirmation
- TC-13: Playwright Browser Automation
"""

import unittest
import requests
import json
import uuid

BASE_URL = "http://localhost:5000"

class TestBusgoSRS(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()

    def test_tc01_user_registration(self):
        """TC-01: User Registration"""
        unique_email = f"test_{uuid.uuid4().hex[:6]}@busgo.com"
        payload = {
            "username": "Test Traveler",
            "email": unique_email,
            "password": "Password123!",
            "phone": "9876543210",
            "role": "customer"
        }
        res = self.session.post(f"{BASE_URL}/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["user"]["email"], unique_email)

    def test_tc02_user_login(self):
        """TC-02: User Login"""
        payload = {
            "email": "srikar@busgo.com",
            "password": "srikar123"
        }
        res = self.session.post(f"{BASE_URL}/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], "srikar@busgo.com")

    def test_tc03_bus_search(self):
        """TC-03: Bus Search (Valid parameters)"""
        res = self.session.get(f"{BASE_URL}/api/buses/search?from=Hyderabad&to=Bangalore")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertGreater(data.get("count", 0), 0)
        first_bus = data["buses"][0]
        self.assertEqual(first_bus["source"], "Hyderabad")
        self.assertEqual(first_bus["destination"], "Bangalore")

    def test_tc04_invalid_search_input(self):
        """TC-04: Invalid Search Input"""
        res = self.session.post(f"{BASE_URL}/api/chat", json={"message": "I want to travel"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("type"), "clarification_needed")
        self.assertIn("Origin City", data.get("reply", ""))

    def test_tc05_price_comparison(self):
        """TC-05: Price Comparison"""
        res = self.session.get(f"{BASE_URL}/api/buses/compare?from=Hyderabad&to=Bangalore&sort_by=cheapest")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        comparison = data.get("comparison_table", [])
        self.assertGreater(len(comparison), 1)
        # Verify sorted by price ascending
        prices = [b["price"] for b in comparison]
        self.assertEqual(prices, sorted(prices))

    def test_tc06_rag_question(self):
        """TC-06: RAG Question (Covered by knowledge base)"""
        payload = {"message": "What is the refund percentage if I cancel 30 hours before travel?"}
        res = self.session.post(f"{BASE_URL}/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("tool_called"), "search_travel_policy")
        self.assertTrue(data.get("grounded"))
        self.assertIn("50%", data.get("reply", ""))
        self.assertIn("Cancellation Refund Policy", data.get("sources", []))

    def test_tc07_unsupported_rag_question(self):
        """TC-07: Unsupported RAG Question"""
        payload = {"query": "What is the capital of Australia?"}
        res = self.session.post(f"{BASE_URL}/api/knowledge/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data.get("grounded"))
        self.assertIn("unavailable in the BUSGO travel policy", data.get("answer", ""))

    def test_tc08_ai_agent_tool_calling(self):
        """TC-08: AI Agent Tool Calling"""
        prompt = "Find a sleeper bus from Hyderabad to Bangalore under 1000 rupees."
        res = self.session.post(f"{BASE_URL}/api/chat", json={"message": prompt})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("tool_called"), "search_bus")
        self.assertGreater(len(data.get("buses", [])), 0)

    def test_tc09_seat_selection(self):
        """TC-09: Seat Selection and Layout Inspection"""
        res = self.session.get(f"{BASE_URL}/api/buses/1/seats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("decks", data)
        self.assertIn("lower", data["decks"])
        self.assertIn("upper", data["decks"])
        self.assertGreater(len(data["seats"]), 20)

    def test_tc10_booking_history(self):
        """TC-10: Booking History for Authenticated User"""
        res = self.session.get(f"{BASE_URL}/api/bookings?user_id=1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("bookings", data)

    def test_tc11_claude_fallback_reliability(self):
        """TC-11: Claude API Reliability and Safe Fallback"""
        # Checks that agent processes complex comparison prompt without error even without API key
        prompt = "Compare the best buses from Mumbai to Pune."
        res = self.session.post(f"{BASE_URL}/api/chat", json={"message": prompt})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("tool_called"), "compare_bus")

    def test_tc12_booking_confirmation(self):
        """TC-12: Booking Confirmation and Status"""
        payload = {
            "user_id": 1,
            "bus_id": 1,
            "passenger_name": "SRS Test Passenger",
            "seat_number": "L18"
        }
        res = self.session.post(f"{BASE_URL}/api/bookings", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data.get("success"))
        booking = data.get("booking", {})
        self.assertEqual(booking.get("status"), "CONFIRMED")
        self.assertTrue(booking.get("pnr", "").startswith("BG"))

    def test_tc13_hcltech_demonstrations(self):
        """Test all 3 Recommended HCLTech Demonstrations"""
        for demo_id in [1, 2, 3]:
            res = self.session.get(f"{BASE_URL}/api/demo/{demo_id}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["demo_id"], demo_id)

    def test_tc14_browser_automation(self):
        """TC-14: Playwright Browser Automation"""
        payload = {"from": "Hyderabad", "to": "Bangalore"}
        res = self.session.post(f"{BASE_URL}/api/automation/run", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("screenshot_base64", "").startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
