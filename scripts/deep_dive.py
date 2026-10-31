import pandas as pd
import numpy as np

df = pd.read_csv('orders_sample.csv')
df['status_clean'] = df['final_status'].astype(str).str.strip().str.upper()

print("--- ADDRESS INVESTIGATION ---")
print("Addresses with length <= 5:")
print(df[df['address'].astype(str).str.len() <= 5][['order_id', 'customer_name', 'address', 'city', 'state', 'status_clean']])
print("Count of length <= 5:", len(df[df['address'].astype(str).str.len() <= 5]))
print("RTO rate of length <= 5:", (df[df['address'].astype(str).str.len() <= 5]['status_clean'] == 'RTO').mean())

print("\nAddresses with length <= 15:")
short_addr = df[df['address'].astype(str).str.len() <= 15]
print("Unique short addresses:", short_addr['address'].value_counts().head(20))
print("Short address RTO rate:", (short_addr['status_clean'] == 'RTO').mean())

print("\n--- FAKE NAMES INVESTIGATION ---")
fake_name_list = ['test', 'asdf', 'na', 'aaa', 'abc', 'test order', 'qwerty', 'dummy', 'fake']
fake_mask = df['customer_name'].astype(str).str.lower().str.strip().isin(fake_name_list)
print("Explicit fake names count:", fake_mask.sum())
print("Explicit fake names RTO rate:", (df[fake_mask]['status_clean'] == 'RTO').mean())
print(df[fake_mask][['customer_name', 'address', 'city', 'order_value', 'status_clean']].head(20))

print("\n--- COMBINED RISK FACTORS ---")
# What if someone has prior_rto >= 1?
print("Prior RTO >= 1 count:", (df['customer_prior_rto'] >= 1).sum())
print("Prior RTO >= 1 RTO rate:", (df[df['customer_prior_rto'] >= 1]['status_clean'] == 'RTO').mean())

# What if prior_rto >= 2?
print("Prior RTO >= 2 count:", (df['customer_prior_rto'] >= 2).sum())
print("Prior RTO >= 2 RTO rate:", (df[df['customer_prior_rto'] >= 2]['status_clean'] == 'RTO').mean())

# High value + Bihar / UP
high_val_bup = df[(df['order_value'] > 1500) & (df['state'].isin(['Bihar', 'Uttar Pradesh']))]
print("High value (>1500) in Bihar/UP count:", len(high_val_bup))
print("High value in Bihar/UP RTO rate:", (high_val_bup['status_clean'] == 'RTO').mean())

# Items analysis
print("\n--- ITEMS ANALYSIS ---")
items_stats = df.groupby('items')['status_clean'].agg(
    total='count',
    rto=lambda s: (s == 'RTO').sum(),
    rto_rate=lambda s: (s == 'RTO').mean()
).sort_values(by='total', ascending=False)
print("Top 15 item combinations:")
print(items_stats.head(15))

# Courier differences by state
print("\n--- COURIER OVERALL PERFORMANCE ---")
courier_stats = df.groupby('courier')['status_clean'].agg(
    total='count',
    rto_rate=lambda s: (s == 'RTO').mean()
).sort_values(by='rto_rate', ascending=False)
print(courier_stats)

# Let's inspect the correlation matrix / predictive power
print("\n--- NUMERIC FEATURES SUMMARY ---")
num_cols = ['order_value', 'num_items', 'customer_prior_orders', 'customer_prior_rto']
for c in num_cols:
    corr = (df['status_clean'] == 'RTO').corr(df[c])
    print(f"Correlation of {c} with RTO: {corr:.4f}")
