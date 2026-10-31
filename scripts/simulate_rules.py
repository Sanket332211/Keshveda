import pandas as pd
import numpy as np
import json

df = pd.read_csv('orders_sample.csv')
df['status_clean'] = df['final_status'].astype(str).str.strip().str.upper()
df['order_datetime'] = pd.to_datetime(df['order_datetime'])
df['month'] = df['order_datetime'].dt.to_period('M')

# Filter valid delivered/rto
valid_df = df[df['status_clean'].isin(['DELIVERED', 'RTO'])].copy()
valid_df['is_rto'] = (valid_df['status_clean'] == 'RTO').astype(int)

# Economics constants
COST_RTO = 169.40  # 65 + 65 + 25 + (0.08 * 180)
MARGIN_RATE = 0.62
CAC = 300.00
PREPAID_DISCOUNT = 50.00  # flat Rs 50 discount
PREPAID_RTO_RATE = 0.04

# WhatsApp conversion assumptions based on industry benchmarks:
# For "Ship after confirmation":
# - Genuine customers confirm: 85% reply 'yes' and get delivered; 15% fail to reply / cancel.
# - RTO-intent / accidental buyers: 70% ignore / cancel; only 30% confirm (and might still RTO).
CONFIRM_GENUINE_CONFIRM_RATE = 0.85
CONFIRM_RTO_CONFIRM_RATE = 0.30

# For "Nudge to prepaid":
# - 25% of customers take the Rs 50 discount and convert to prepaid!
# - For those who convert to prepaid, RTO rate drops to 4%.
# - Remaining 75% who stay COD are put through WhatsApp confirmation.
NUDGE_PREPAID_CONVERSION_RATE = 0.25

# Let's inspect the baseline of last month (September 2026)
sep_df = valid_df[valid_df['month'] == '2026-09'].copy()
print(f"=== SEPTEMBER 2026 BASELINE ===")
print(f"Total orders: {len(sep_df)}")
sep_rto_count = sep_df['is_rto'].sum()
sep_del_count = len(sep_df) - sep_rto_count
print(f"Delivered: {sep_del_count} ({sep_del_count/len(sep_df):.1%})")
print(f"RTO: {sep_rto_count} ({sep_rto_count/len(sep_df):.1%})")
sep_gross_margin = (sep_df[sep_df['is_rto'] == 0]['order_value'] * MARGIN_RATE).sum()
sep_rto_loss = sep_rto_count * COST_RTO
print(f"Gross margin realized: Rs {sep_gross_margin:,.2f}")
print(f"Direct RTO loss: Rs {sep_rto_loss:,.2f}")
print(f"Net realized contribution: Rs {sep_gross_margin - sep_rto_loss:,.2f}")

# Define decision rules
def evaluate_order(row, thresholds):
    order_val = row['order_value']
    prior_orders = row['customer_prior_orders']
    prior_rto = row['customer_prior_rto']
    state = str(row['state'])
    addr = str(row['address']).strip()
    name = str(row['customer_name']).strip().lower()
    phone = str(row['phone']).strip()
    
    # 1. Bogus / Fake / Malicious checks
    fake_names = {'test', 'asdf', 'na', 'aaa', 'abc', 'test order', 'qwerty', 'dummy', 'fake'}
    is_fake_name = name in fake_names or len(name) <= 2
    is_dummy_addr = addr.lower() in {'.', 'xyz', 'home', 'call me', 'delhi', 'mumbai', 'patna'} or len(addr) <= 4
    is_invalid_phone = len(phone) != 10 or not phone.isdigit() or phone[0] not in '6789'
    
    # Check 1: Blatant Fake -> HOLD / CANCEL
    if is_fake_name or is_dummy_addr or is_invalid_phone:
        return 'Hold / cancel', 95, "Flagged fake/incomplete details (invalid address, fake name, or malformed phone)"
    
    # Check 2: Chronic RTO offender -> HOLD / CANCEL
    if prior_rto >= thresholds['cancel_prior_rto_threshold']:  # default >= 2
        return 'Hold / cancel', 85, f"High RTO history ({prior_rto} previous returns)"
    
    # Check 3: High value + High risk geography -> NUDGE TO PREPAID
    high_risk_states = thresholds['high_risk_states']  # Bihar, UP, MP
    if state in high_risk_states and order_val >= thresholds['nudge_high_risk_state_value']:
        return 'Nudge to prepaid', 65, f"High order value (Rs {order_val}) in high-RTO region ({state})"
    
    if order_val >= thresholds['nudge_general_value']:  # default >= 1500
        return 'Nudge to prepaid', 60, f"High ticket size (Rs {order_val}) on COD"
    
    # Check 4: Medium risk address or prior RTO=1 -> SHIP AFTER CONFIRMATION
    has_house_num = bool(pd.Series([addr]).str.contains(r'\d+', regex=True).iloc[0])
    is_short_addr = len(addr) < thresholds['short_addr_threshold']  # e.g. < 25
    
    if prior_rto == 1:
        return 'Ship after confirmation', 55, "Customer has 1 prior RTO history; requires address & intent re-verification"
    
    if not has_house_num or is_short_addr:
        return 'Ship after confirmation', 50, "Address lacks specific house/flat number or is very brief; requires landmark confirmation"
        
    if state in high_risk_states and prior_orders == 0:
        return 'Ship after confirmation', 45, f"First-time buyer in {state}; requires WhatsApp delivery confirmation"

    # Default -> SHIP AS-IS
    return 'Ship as-is', 15, "Low risk profile: verified address, clean customer history"

thresholds = {
    'cancel_prior_rto_threshold': 2,
    'high_risk_states': ['Bihar', 'Uttar Pradesh', 'Madhya Pradesh'],
    'nudge_high_risk_state_value': 800,
    'nudge_general_value': 1500,
    'short_addr_threshold': 25
}

# Run evaluation on September 2026
actions = []
scores = []
reasons = []

for idx, row in sep_df.iterrows():
    act, sc, rsn = evaluate_order(row, thresholds)
    actions.append(act)
    scores.append(sc)
    reasons.append(rsn)

sep_df['action'] = actions
sep_df['risk_score'] = scores
sep_df['reason'] = reasons

print("\n=== SEPTEMBER 2026 ACTION BUCKETS ===")
print(sep_df['action'].value_counts())
print("\nAction breakdown by actual delivery status:")
print(pd.crosstab(sep_df['action'], sep_df['status_clean'], margins=True))

# Financial Impact Simulation on September 2026:
# 1. Hold / Cancel:
cancelled = sep_df[sep_df['action'] == 'Hold / cancel']
avoided_rto_cancel = (cancelled['status_clean'] == 'RTO').sum()
false_cancel = (cancelled['status_clean'] == 'DELIVERED').sum()
savings_from_cancel = avoided_rto_cancel * COST_RTO
lost_margin_cancel = (cancelled[cancelled['status_clean'] == 'DELIVERED']['order_value'] * MARGIN_RATE).sum()
lost_cac_cancel = false_cancel * CAC

print(f"\n--- CANCEL IMPACT ---")
print(f"Total Cancelled: {len(cancelled)}")
print(f"Correctly avoided RTOs: {avoided_rto_cancel}")
print(f"False cancellations (would have delivered): {false_cancel}")
print(f"Logistics savings: Rs {savings_from_cancel:,.2f}")
print(f"Gross margin lost from false cancel: Rs {lost_margin_cancel:,.2f}")
print(f"Net profit impact of cancellation: Rs {savings_from_cancel - lost_margin_cancel:,.2f}")

# Let's do the full simulation across all 4 buckets
# For Ship as-is:
ship_as_is = sep_df[sep_df['action'] == 'Ship as-is']
ship_rto = (ship_as_is['status_clean'] == 'RTO').sum()
ship_del = (ship_as_is['status_clean'] == 'DELIVERED').sum()

# For Ship after confirmation:
# Genuine: 85% confirm and deliver; 15% unconfirmed (avoided fulfillment)
# RTO: 30% confirm (and RTO); 70% unconfirmed (avoided RTO!)
confirm_df = sep_df[sep_df['action'] == 'Ship after confirmation']
confirm_gen_total = (confirm_df['status_clean'] == 'DELIVERED').sum()
confirm_rto_total = (confirm_df['status_clean'] == 'RTO').sum()

avoided_rto_confirm = confirm_rto_total * (1 - CONFIRM_RTO_CONFIRM_RATE)
shipped_rto_confirm = confirm_rto_total * CONFIRM_RTO_CONFIRM_RATE
delivered_confirm = confirm_gen_total * CONFIRM_GENUINE_CONFIRM_RATE
lost_gen_confirm = confirm_gen_total * (1 - CONFIRM_GENUINE_CONFIRM_RATE)

# For Nudge to prepaid:
# 25% convert to prepaid -> RTO drops to 4%.
# 75% stay COD and go to confirmation.
nudge_df = sep_df[sep_df['action'] == 'Nudge to prepaid']
nudge_total = len(nudge_df)
nudge_gen_total = (nudge_df['status_clean'] == 'DELIVERED').sum()
nudge_rto_total = (nudge_df['status_clean'] == 'RTO').sum()

converted_prepaid = nudge_total * NUDGE_PREPAID_CONVERSION_RATE
prepaid_discounts_paid = converted_prepaid * PREPAID_DISCOUNT

# Overall RTO reduction:
total_baseline_rto = sep_rto_count
total_avoided_rto = avoided_rto_cancel + avoided_rto_confirm + (nudge_rto_total * NUDGE_PREPAID_CONVERSION_RATE * (1 - PREPAID_RTO_RATE/0.28))
total_savings = total_avoided_rto * COST_RTO

print(f"\n--- OVERALL SEPTEMBER 2026 SIMULATION SUMMARY ---")
print(f"Baseline RTOs: {total_baseline_rto} ({total_baseline_rto/len(sep_df):.1%})")
print(f"Total Avoided RTOs: {total_avoided_rto:.1f}")
print(f"Estimated Gross Logistics Savings: Rs {total_savings:,.2f}")
print(f"Estimated Lost Margin from Drop-offs/Cancellations: Rs {lost_margin_cancel + (lost_gen_confirm * 649 * MARGIN_RATE):,.2f}")

