"""
Core Decision Engine for COD Orders
Evaluates incoming COD orders and outputs one of 4 actions:
1. Ship as-is
2. Ship after confirmation (WhatsApp)
3. Nudge to prepaid (Discount)
4. Hold / cancel

Configurable thresholds loaded dynamically from config/thresholds.json without touching code.
"""

import os
import json
import re
from typing import Dict, Any, Tuple, Optional
import pandas as pd

from engine.llm_verifier import LLMAddressVerifier
from engine.financial_model import FinancialConfig, SimulationEngine


class DecisionEngine:
    """Takes an incoming order dict and classifies it into one of four operational buckets."""

    def __init__(self, config_path: str = "config/thresholds.json"):
        self.config_path = config_path
        self.thresholds = self._load_thresholds()
        self.llm_verifier = LLMAddressVerifier()
        self.financial_config = FinancialConfig(**self.thresholds.get("financial_assumptions", {}))
        self.simulator = SimulationEngine(
            self.financial_config,
            self.thresholds.get("whatsapp_funnel_assumptions", {})
        )

    def _load_thresholds(self) -> Dict[str, Any]:
        """Loads configuration JSON safely."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "operational_thresholds": {
                "cancel_min_prior_rto": 2,
                "nudge_high_risk_state_min_order_value": 800,
                "nudge_general_min_order_value": 1500,
                "confirm_short_address_length": 25,
                "high_risk_states": ["Bihar", "Uttar Pradesh", "Madhya Pradesh"],
                "high_rto_couriers": ["Xpressbees", "Ecom Express"],
                "auto_cancel_unresponsive_hours": 24,
                "require_confirmation_for_first_time_high_risk": True
            }
        }

    def reload_config(self):
        """Reloads configuration from disk (used by dashboard when thresholds are updated)."""
        self.thresholds = self._load_thresholds()
        self.financial_config = FinancialConfig(**self.thresholds.get("financial_assumptions", {}))
        self.simulator = SimulationEngine(
            self.financial_config,
            self.thresholds.get("whatsapp_funnel_assumptions", {})
        )

    def evaluate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single COD order and returns the action, risk score, plain-English reason,
        and full audit log.
        """
        ops_cfg = self.thresholds.get("operational_thresholds", {})
        high_risk_states = set(ops_cfg.get("high_risk_states", ["Bihar", "Uttar Pradesh", "Madhya Pradesh"]))
        cancel_prior_rto = ops_cfg.get("cancel_min_prior_rto", 2)
        nudge_state_val = ops_cfg.get("nudge_high_risk_state_min_order_value", 800)
        nudge_general_val = ops_cfg.get("nudge_general_min_order_value", 1500)
        short_addr_len = ops_cfg.get("confirm_short_address_length", 25)

        # Extract fields
        order_id = str(order.get("order_id", "UNKNOWN"))
        customer_name = str(order.get("customer_name", "")).strip()
        phone = str(order.get("phone", "")).strip()
        address = str(order.get("address", "")).strip()
        city = str(order.get("city", "")).strip()
        state = str(order.get("state", "")).strip()
        pincode = order.get("pincode")
        order_value = float(order.get("order_value", 0))
        prior_orders = int(order.get("customer_prior_orders", 0))
        prior_rto = int(order.get("customer_prior_rto", 0))
        courier = str(order.get("courier", "")).strip()

        # Step 1: Call LLM Verifier for Address & Name semantics
        llm_result = self.llm_verifier.verify_order(customer_name, address, city, state)

        # Step 2: Deterministic Rule Checks & Score Accumulator
        triggers = []
        risk_score = 20  # baseline COD risk (~20%)

        # Phone number validation
        phone_digits = re.sub(r'\D', '', phone)
        is_invalid_phone = False
        if len(phone_digits) != 10 or phone_digits[0] not in '6789':
            # Check if 12 digits starting with 91
            if len(phone_digits) == 12 and phone_digits.startswith('91') and phone_digits[2] in '6789':
                phone_digits = phone_digits[2:]  # valid with country code
            else:
                is_invalid_phone = True
                triggers.append("Invalid 10-digit mobile number format")
                risk_score += 40

        # LLM Name & Address triggers
        if not llm_result["is_real_name"]:
            triggers.append(f"Suspicious customer name ({llm_result['name_issue']})")
            risk_score += 45

        if llm_result["is_dummy_address"]:
            triggers.append(f"Dummy or placeholder address ('{address}')")
            risk_score += 55
        elif not llm_result["has_house_or_flat"]:
            if llm_result["has_landmark"]:
                triggers.append(f"Landmark provided but missing flat/house number")
                risk_score += 20
            else:
                triggers.append("Vague address missing both premise number and landmark")
                risk_score += 35

        # Geographic risk
        if state in high_risk_states:
            triggers.append(f"High-RTO geographic zone ({state})")
            risk_score += 25

        # Customer History
        if prior_rto >= cancel_prior_rto:
            triggers.append(f"Chronic return history ({prior_rto} previous RTOs)")
            risk_score += 50
        elif prior_rto == 1:
            triggers.append("Customer has 1 prior RTO on record")
            risk_score += 25
        elif prior_orders >= 1 and prior_rto == 0:
            triggers.append(f"Trusted repeat buyer ({prior_orders} delivered orders, 0 returns)")
            risk_score -= 30

        # Order Value Risk
        if order_value >= nudge_general_val:
            triggers.append(f"High COD ticket size (₹{order_value:,.0f} > ₹{nudge_general_val:,.0f})")
            risk_score += 25
        elif state in high_risk_states and order_value >= nudge_state_val:
            triggers.append(f"Elevated ticket size in high-risk zone (₹{order_value:,.0f} in {state})")
            risk_score += 20

        # Clamp risk score
        risk_score = max(5, min(99, risk_score))

        # Step 3: Action Classification Logic
        # Action 4: HOLD / CANCEL
        # Applied ONLY when:
        # A) Blatant bogus order (dummy address AND fake name or invalid phone)
        # B) Customer has >= 2 prior RTOs
        if (llm_result["is_dummy_address"] and (not llm_result["is_real_name"] or is_invalid_phone)) or (prior_rto >= cancel_prior_rto):
            action = "Hold / cancel"
            if prior_rto >= cancel_prior_rto:
                reason = f"Repeat RTO offender ({prior_rto} previous returns). Held to prevent guaranteed shipping loss."
            elif llm_result["is_dummy_address"] and not llm_result["is_real_name"]:
                reason = f"Blatant test/fake order with placeholder name ('{customer_name}') and unusable address ('{address}')."
            else:
                reason = f"Undeliverable address ('{address}') coupled with an uncontactable phone number ({phone})."

        # Action 3: NUDGE TO PREPAID
        # Applied when order value is high, especially in Tier-2/3 high RTO zones.
        elif (order_value >= nudge_general_val) or (state in high_risk_states and order_value >= nudge_state_val):
            action = "Nudge to prepaid"
            if state in high_risk_states:
                reason = f"High ticket size (₹{order_value:,.0f}) in {state} carries high RTO risk. Nudge to prepaid with ₹50 discount locks delivery."
            else:
                reason = f"Large COD order (₹{order_value:,.0f}). Offering prepaid discount reduces cash handling risk and guarantees delivery."

        # Action 2: SHIP AFTER CONFIRMATION
        # Applied for moderate risk: incomplete address, prior RTO=1, or first-time buyer in high-RTO state.
        elif (risk_score >= 40) or (llm_result["address_quality_score"] < 65) or (prior_rto == 1) or (state in high_risk_states and prior_orders == 0):
            action = "Ship after confirmation"
            if not llm_result["has_house_or_flat"]:
                reason = f"Address lacks house/flat number. Sending WhatsApp verification to confirm exact doorstep directions before dispatch."
            elif prior_rto == 1:
                reason = f"Customer had 1 previous return. WhatsApp confirmation required to re-verify purchase intent."
            elif state in high_risk_states and prior_orders == 0:
                reason = f"First-time buyer in {state}. Dispatch held pending 1-click WhatsApp delivery confirmation."
            else:
                reason = f"Moderate risk detected (Score {risk_score}). WhatsApp confirmation verifies address and locks buyer commitment."

        # Action 1: SHIP AS-IS
        # Low risk, complete address, trusted customer, or low order value in stable geography.
        else:
            action = "Ship as-is"
            if prior_orders > 0 and prior_rto == 0:
                reason = f"Verified repeat customer with flawless delivery track record ({prior_orders} orders). Instant dispatch."
            else:
                reason = f"Clean delivery profile: complete address ({llm_result['address_quality_score']}/100), verified phone, low risk zone."

        # Expected unit economics
        gross_margin = order_value * self.financial_config.gross_margin_rate
        expected_rto_cost = (risk_score / 100.0) * self.financial_config.direct_rto_cost

        return {
            "order_id": order_id,
            "action": action,
            "risk_score": risk_score,
            "reason": reason,
            "triggers": triggers,
            "llm_analysis": llm_result,
            "economics": {
                "order_value": order_value,
                "gross_margin": round(gross_margin, 2),
                "expected_rto_cost": round(expected_rto_cost, 2),
                "breakeven_risk_threshold_pct": round(self.financial_config.breakeven_rto_probability * 100, 1)
            }
        }

    def evaluate_batch(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Evaluates an entire DataFrame of orders and returns annotated DataFrame + financial simulation."""
        results = []
        for _, row in df.iterrows():
            eval_res = self.evaluate_order(row.to_dict())
            results.append({
                "action": eval_res["action"],
                "risk_score": eval_res["risk_score"],
                "reason": eval_res["reason"],
                "address_quality_score": eval_res["llm_analysis"]["address_quality_score"],
                "is_dummy_address": eval_res["llm_analysis"]["is_dummy_address"],
                "is_real_name": eval_res["llm_analysis"]["is_real_name"]
            })

        res_df = pd.DataFrame(results, index=df.index)
        annotated_df = pd.concat([df, res_df], axis=1)

        simulation = self.simulator.simulate(annotated_df)
        return annotated_df, simulation

