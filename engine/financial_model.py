"""
Financial Model & Unit Economics for D2C COD Decision Engine
Calculates exact rupee (₹) impacts, trade-offs, and simulations.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd


@dataclass
class FinancialConfig:
    forward_shipping_cost: float = 65.0
    return_shipping_cost: float = 65.0
    packaging_handling_cost: float = 25.0
    damage_probability: float = 0.08
    average_product_cost: float = 180.0
    average_order_value: float = 649.0
    gross_margin_rate: float = 0.62
    customer_acquisition_cost: float = 300.0
    prepaid_discount_amount: float = 50.0
    prepaid_rto_rate: float = 0.04

    @property
    def direct_rto_cost(self) -> float:
        """
        Total cash lost on every RTO:
        Forward shipping (₹65) + Return shipping (₹65) + Packaging (₹25) + Expected damage (8% * ₹180)
        = ₹169.40
        """
        return (
            self.forward_shipping_cost
            + self.return_shipping_cost
            + self.packaging_handling_cost
            + (self.damage_probability * self.average_product_cost)
        )

    @property
    def gross_profit_per_order(self) -> float:
        """Average gross profit on a delivered order (62% of ₹649 = ₹402.38)"""
        return self.average_order_value * self.gross_margin_rate

    @property
    def false_cancellation_loss(self) -> float:
        """
        True financial loss when a genuine order is cancelled:
        Forfeited Gross Profit (₹402.38) + Sunk Acquisition Cost (₹300.00) = ₹702.38
        """
        return self.gross_profit_per_order + self.customer_acquisition_cost

    @property
    def cancellation_to_rto_cost_ratio(self) -> float:
        """Ratio of false cancellation loss to RTO cost (702.38 / 169.40 = 4.15x)"""
        return self.false_cancellation_loss / self.direct_rto_cost

    @property
    def breakeven_rto_probability(self) -> float:
        """
        The RTO risk threshold above which shipping has negative expected value:
        (1 - p) * GrossProfit - p * DirectRtoCost = 0
        p = GrossProfit / (GrossProfit + DirectRtoCost) = 402.38 / 571.78 = ~70.36%
        """
        return self.gross_profit_per_order / (self.gross_profit_per_order + self.direct_rto_cost)

    def calculate_prepaid_discount_roi(self, cod_rto_risk: float) -> Dict[str, float]:
        """
        Calculates unit economics of offering a prepaid discount.
        Example: At 45% COD RTO risk, expected COD RTO cost is ₹76.23.
        On prepaid (4% RTO), expected RTO cost is ₹6.78.
        Gross savings = ₹69.45.
        With a ₹50 discount, brand gains +₹19.45 net cash per converted order!
        """
        expected_cod_rto_loss = cod_rto_risk * self.direct_rto_cost
        expected_prepaid_rto_loss = self.prepaid_rto_rate * self.direct_rto_cost
        rto_savings = expected_cod_rto_loss - expected_prepaid_rto_loss
        net_profit_gain = rto_savings - self.prepaid_discount_amount
        return {
            "cod_rto_risk": cod_rto_risk,
            "expected_cod_loss": round(expected_cod_rto_loss, 2),
            "expected_prepaid_loss": round(expected_prepaid_rto_loss, 2),
            "gross_rto_savings": round(rto_savings, 2),
            "discount_offered": round(self.prepaid_discount_amount, 2),
            "net_gain_per_conversion": round(net_profit_gain, 2),
            "is_profitable": net_profit_gain > 0
        }


class SimulationEngine:
    """Simulates financial impact of decision rules on historical batches."""

    def __init__(self, config: FinancialConfig, funnel_config: Dict[str, float] = None):
        self.config = config
        self.funnel = funnel_config or {
            "genuine_customer_confirmation_rate": 0.85,
            "rto_intent_confirmation_rate": 0.30,
            "prepaid_nudge_conversion_rate": 0.25
        }

    def simulate(self, df_evaluated: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluates a DataFrame that has columns:
        'action' (Ship as-is, Ship after confirmation, Nudge to prepaid, Hold / cancel),
        'status_clean' or 'final_status' (DELIVERED, RTO),
        'order_value'.
        """
        df = df_evaluated.copy()
        if 'status_clean' not in df.columns and 'final_status' in df.columns:
            df['status_clean'] = df['final_status'].astype(str).str.strip().str.upper()

        total_orders = len(df)
        if total_orders == 0:
            return {}

        baseline_rto = (df['status_clean'] == 'RTO').sum()
        baseline_delivered = (df['status_clean'] == 'DELIVERED').sum()
        baseline_rto_rate = baseline_rto / total_orders if total_orders else 0
        baseline_gross_margin = (df[df['status_clean'] == 'DELIVERED']['order_value'] * self.config.gross_margin_rate).sum()
        baseline_rto_loss = baseline_rto * self.config.direct_rto_cost
        baseline_net_contribution = baseline_gross_margin - baseline_rto_loss

        # Bucket Breakdown
        bucket_counts = df['action'].value_counts().to_dict()
        for b in ['Ship as-is', 'Ship after confirmation', 'Nudge to prepaid', 'Hold / cancel']:
            bucket_counts.setdefault(b, 0)

        # 1. Hold / cancel bucket analysis
        cancelled = df[df['action'] == 'Hold / cancel']
        avoided_rto_cancel = (cancelled['status_clean'] == 'RTO').sum()
        false_cancel_count = (cancelled['status_clean'] == 'DELIVERED').sum()
        savings_from_cancel = avoided_rto_cancel * self.config.direct_rto_cost
        lost_margin_cancel = (cancelled[cancelled['status_clean'] == 'DELIVERED']['order_value'] * self.config.gross_margin_rate).sum()
        lost_cac_cancel = false_cancel_count * self.config.customer_acquisition_cost

        # 2. Ship after confirmation bucket analysis
        # Genuine: genuine_confirmation_rate confirm and deliver; remainder drop off.
        # RTO intent: rto_confirmation_rate confirm (and turn into RTO); remainder (1 - rate) don't confirm -> avoided RTO!
        confirm_df = df[df['action'] == 'Ship after confirmation']
        confirm_gen = (confirm_df['status_clean'] == 'DELIVERED').sum()
        confirm_rto = (confirm_df['status_clean'] == 'RTO').sum()

        gen_confirm_rate = self.funnel['genuine_customer_confirmation_rate']
        rto_confirm_rate = self.funnel['rto_intent_confirmation_rate']

        avoided_rto_confirm = confirm_rto * (1.0 - rto_confirm_rate)
        shipped_rto_confirm = confirm_rto * rto_confirm_rate
        delivered_confirm = confirm_gen * gen_confirm_rate
        lost_gen_confirm = confirm_gen * (1.0 - gen_confirm_rate)
        savings_from_confirm = avoided_rto_confirm * self.config.direct_rto_cost
        lost_margin_confirm = (confirm_df[confirm_df['status_clean'] == 'DELIVERED']['order_value'] * self.config.gross_margin_rate).mean() * lost_gen_confirm if lost_gen_confirm else 0.0

        # 3. Nudge to prepaid bucket analysis
        # prepaid_conversion_rate convert to prepaid -> RTO drops to prepaid_rto_rate (4%)
        # Remainder (1 - conversion_rate) proceed with confirmation flow
        nudge_df = df[df['action'] == 'Nudge to prepaid']
        nudge_total = len(nudge_df)
        nudge_gen = (nudge_df['status_clean'] == 'DELIVERED').sum()
        nudge_rto = (nudge_df['status_clean'] == 'RTO').sum()

        conv_rate = self.funnel['prepaid_nudge_conversion_rate']
        converted_prepaid = nudge_total * conv_rate
        discounts_granted = converted_prepaid * self.config.prepaid_discount_amount

        # On converted orders: RTO drops from ~rto% to 4%
        rto_rate_in_nudge = (nudge_rto / nudge_total) if nudge_total else 0.28
        avoided_rto_prepaid = (nudge_rto * conv_rate) * (1.0 - (self.config.prepaid_rto_rate / max(0.01, rto_rate_in_nudge)))
        avoided_rto_prepaid = max(0.0, avoided_rto_prepaid)

        # For remaining unconverted nudge orders (1 - conv_rate):
        unconverted_rto = nudge_rto * (1.0 - conv_rate)
        avoided_rto_nudge_unconv = unconverted_rto * (1.0 - rto_confirm_rate)

        total_avoided_rto_nudge = avoided_rto_prepaid + avoided_rto_nudge_unconv
        savings_from_nudge = total_avoided_rto_nudge * self.config.direct_rto_cost

        # 4. Ship as-is bucket analysis
        ship_as_is = df[df['action'] == 'Ship as-is']
        shipped_as_is_rto = (ship_as_is['status_clean'] == 'RTO').sum()
        shipped_as_is_del = (ship_as_is['status_clean'] == 'DELIVERED').sum()

        # Totals
        total_avoided_rto = avoided_rto_cancel + avoided_rto_confirm + total_avoided_rto_nudge
        post_rto_count = baseline_rto - total_avoided_rto
        post_rto_rate = post_rto_count / total_orders if total_orders else 0

        total_savings_rto = total_avoided_rto * self.config.direct_rto_cost
        total_lost_margin = lost_margin_cancel + lost_margin_confirm
        total_discounts = discounts_granted

        net_rupee_impact = total_savings_rto - total_lost_margin - total_discounts

        return {
            "total_orders": total_orders,
            "baseline": {
                "delivered": int(baseline_delivered),
                "rto": int(baseline_rto),
                "rto_rate_pct": round(baseline_rto_rate * 100, 1),
                "gross_margin": round(baseline_gross_margin, 2),
                "rto_loss": round(baseline_rto_loss, 2),
                "net_contribution": round(baseline_net_contribution, 2)
            },
            "buckets": bucket_counts,
            "intervention_metrics": {
                "avoided_rto_count": round(total_avoided_rto, 1),
                "new_projected_rto_rate_pct": round(post_rto_rate * 100, 1),
                "rto_reduction_pct": round((total_avoided_rto / max(1, baseline_rto)) * 100, 1),
                "false_cancellations": int(false_cancel_count),
                "prepaid_conversions": round(converted_prepaid, 1)
            },
            "financial_impact_rupees": {
                "gross_rto_savings": round(total_savings_rto, 2),
                "lost_margin_from_false_cancellations_and_dropoffs": round(total_lost_margin, 2),
                "prepaid_discounts_incurred": round(total_discounts, 2),
                "net_rupee_gain": round(net_rupee_impact, 2)
            }
        }

