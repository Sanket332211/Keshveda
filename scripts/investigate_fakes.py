import pandas as pd
import numpy as np

df = pd.read_csv('orders_sample.csv')
df['status_clean'] = df['final_status'].astype(str).str.strip().str.upper()
valid_df = df[df['status_clean'].isin(['DELIVERED', 'RTO'])].copy()

COST_RTO = 169.40
MARGIN_RATE = 0.62
CAC = 300.00

# Let's inspect which orders in the entire dataset have status == DELIVERED among fake names or dummy addresses:
fake_names = {'test', 'asdf', 'na', 'aaa', 'abc', 'test order', 'qwerty', 'dummy', 'fake'}
dummy_addrs = {'.', 'xyz', 'home', 'call me'}

print("Orders with dummy address AND fake name:")
blatant_bogus = valid_df[
    valid_df['customer_name'].astype(str).str.lower().str.strip().isin(fake_names) &
    valid_df['address'].astype(str).str.lower().str.strip().isin(dummy_addrs)
]
print("Count:", len(blatant_bogus))
print(blatant_bogus['status_clean'].value_counts())

print("\nOrders with dummy address alone:")
dummy_addr_only = valid_df[valid_df['address'].astype(str).str.lower().str.strip().isin(dummy_addrs)]
print("Count:", len(dummy_addr_only))
print(dummy_addr_only['status_clean'].value_counts())

print("\nOrders with invalid phone (< 10 digits or not starting with 6-9):")
invalid_phones = valid_df[~valid_df['phone'].astype(str).str.match(r'^[6-9]\d{9}$')]
print("Count:", len(invalid_phones))
print(invalid_phones['status_clean'].value_counts())

