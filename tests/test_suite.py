"""
Comprehensive Test Suite for Keshveda COD Decision Engine & WhatsApp Flow
Uses Python's standard unittest framework (zero external test dependencies).
"""

import unittest
import json
import os
import sys

# Ensure current working directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd

from engine.decision_engine import DecisionEngine
from engine.financial_model import FinancialConfig, SimulationEngine
from engine.llm_verifier import LLMAddressVerifier
from whatsapp.flow_manager import FlowManager
from app import app


class TestDecisionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DecisionEngine(config_path="config/thresholds.json")

    def test_ship_as_is_for_trusted_customer(self):
        order = {
            "order_id": "T1",
            "customer_name": "Priya Sharma",
            "phone": "9876543210",
            "address": "Flat 401, Golden Towers, Sector 15",
            "city": "Mumbai",
            "state": "Maharashtra",
            "order_value": 649,
            "customer_prior_orders": 2,
            "customer_prior_rto": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Ship as-is")
        self.assertLessEqual(res["risk_score"], 25)

    def test_hold_cancel_for_blatant_bogus(self):
        order = {
            "order_id": "T2",
            "customer_name": "asdf",
            "phone": "9876543210",
            "address": ".",
            "city": "Patna",
            "state": "Bihar",
            "order_value": 899,
            "customer_prior_orders": 0,
            "customer_prior_rto": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Hold / cancel")
        self.assertGreaterEqual(res["risk_score"], 80)

    def test_hold_cancel_for_chronic_rto(self):
        order = {
            "order_id": "T3",
            "customer_name": "Rohan Kumar",
            "phone": "9876543210",
            "address": "House 12, Main Bazar",
            "city": "Delhi",
            "state": "Delhi",
            "order_value": 649,
            "customer_prior_orders": 2,
            "customer_prior_rto": 2
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Hold / cancel")
        self.assertIn("Repeat RTO offender", res["reason"])

    def test_nudge_to_prepaid_for_high_ticket_high_risk_state(self):
        order = {
            "order_id": "T4",
            "customer_name": "Sneha Gupta",
            "phone": "9876543210",
            "address": "House 15, Gandhi Nagar",
            "city": "Patna",
            "state": "Bihar",
            "order_value": 1200,
            "customer_prior_orders": 0,
            "customer_prior_rto": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Nudge to prepaid")

    def test_ship_after_confirmation_for_incomplete_address(self):
        order = {
            "order_id": "T5",
            "customer_name": "Ananya Joshi",
            "phone": "9876543210",
            "address": "Link chowk se left, SBI Bank ke saamne",
            "city": "Indore",
            "state": "Madhya Pradesh",
            "order_value": 649,
            "customer_prior_orders": 0,
            "customer_prior_rto": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Ship after confirmation")
        self.assertTrue(res["llm_analysis"]["has_landmark"])
        self.assertFalse(res["llm_analysis"]["has_house_or_flat"])


class TestFinancialModel(unittest.TestCase):

    def setUp(self):
        self.config = FinancialConfig()

    def test_direct_rto_cost_calculation(self):
        # 65 + 65 + 25 + (0.08 * 180) = 169.40
        self.assertAlmostEqual(self.config.direct_rto_cost, 169.40, places=2)

    def test_gross_profit_per_order(self):
        # 62% of 649 = 402.38
        self.assertAlmostEqual(self.config.gross_profit_per_order, 402.38, places=2)

    def test_false_cancellation_loss(self):
        # 402.38 + 300 = 702.38
        self.assertAlmostEqual(self.config.false_cancellation_loss, 702.38, places=2)

    def test_breakeven_rto_probability(self):
        # 402.38 / (402.38 + 169.40) = ~70.36%
        self.assertAlmostEqual(self.config.breakeven_rto_probability, 0.7036, places=3)

    def test_prepaid_discount_roi(self):
        # At 45% RTO risk: COD loss = 76.23, Prepaid loss = 6.78. Savings = 69.45.
        # With Rs 50 discount -> Net gain = Rs 19.45.
        res = self.config.calculate_prepaid_discount_roi(cod_rto_risk=0.45)
        self.assertTrue(res["is_profitable"])
        self.assertAlmostEqual(res["net_gain_per_conversion"], 19.45, places=1)


class TestWhatsAppFlow(unittest.TestCase):

    def setUp(self):
        self.flow = FlowManager()
        self.sample_order = {
            "order_id": "ORD999",
            "customer_name": "Kavita Roy",
            "phone": "9811122233",
            "address": "Opposite Railway Station",
            "city": "Jaipur",
            "state": "Rajasthan",
            "pincode": 302001,
            "order_value": 749,
            "items": "Hair Oil 100ml"
        }

    def test_flow_confirmation_yes(self):
        session = self.flow.create_session(self.sample_order, action="Ship after confirmation")
        self.assertEqual(session["state"], "AWAITING_REPLY")

        updated = self.flow.process_incoming_message(session, "1")
        self.assertEqual(updated["state"], "CONFIRMED_BY_CUSTOMER")
        self.assertEqual(updated["dispatch_status"], "APPROVED_FOR_DISPATCH")

    def test_flow_cancellation_no(self):
        session = self.flow.create_session(self.sample_order, action="Ship after confirmation")
        updated = self.flow.process_incoming_message(session, "cancel kar do")
        self.assertEqual(updated["state"], "CANCELLED_BY_CUSTOMER")
        self.assertEqual(updated["dispatch_status"], "CANCELLED_AVOIDED_RTO")

    def test_flow_address_update(self):
        session = self.flow.create_session(self.sample_order, action="Ship after confirmation")
        updated = self.flow.process_incoming_message(session, "Flat 204, Shiv Mandir ke paas")
        self.assertEqual(updated["state"], "CONFIRMED_WITH_UPDATED_ADDRESS")
        self.assertIn("Flat 204", updated["current_address"])

    def test_flow_auto_cancel_timer(self):
        session = self.flow.create_session(self.sample_order, action="Ship after confirmation")
        updated = self.flow.trigger_timer_event(session, "24h_auto_cancel")
        self.assertEqual(updated["state"], "EXPIRED_AUTO_CANCEL")


class TestFlaskEndpoints(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_summary_api(self):
        response = self.client.get('/api/summary?time_filter=last_month')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("simulation", data)
        self.assertIn("sample_orders", data)
        self.assertEqual(data["time_filter"], "last_month")

    def test_evaluate_order_api(self):
        order = {
            "order_id": "API_TEST",
            "customer_name": "Test Customer",
            "phone": "9812345678",
            "address": "Plot 10, MG Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "order_value": 500,
            "customer_prior_orders": 1,
            "customer_prior_rto": 0
        }
        response = self.client.post('/api/evaluate_order', json=order)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("action", data)
        self.assertIn("risk_score", data)


if __name__ == "__main__":
    unittest.main()
