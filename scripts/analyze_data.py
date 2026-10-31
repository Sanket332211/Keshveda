import pandas as pd
import numpy as np
import re

df = pd.read_csv('orders_sample.csv')
df['status_clean'] = df['final_status'].astype(str).str.strip().str.upper()

print("=== CLEAN STATUS DISTRIBUTION ===")
print(df['status_clean'].value_counts())
print(df['status_clean'].value_counts(normalize=True))

print("\n=== ZERO ORDER VALUE ROWS ===")
print(df[df['order_value'] == 0][['order_id', 'customer_name', 'address', 'order_value', 'items', 'status_clean']])

print("\n=== MISSING PINCODE ROWS ===")
print(df[df['pincode'].isnull()][['order_id', 'city', 'state', 'address', 'status_clean']])
print("Missing pincode RTO rate:", (df[df['pincode'].isnull()]['status_clean'] == 'RTO').mean())

print("\n=== MISSING CITY ROWS ===")
print(df[df['city'].isnull()][['order_id', 'state', 'address', 'status_clean']])

print("\n=== PHONE NUMBER ANALYSIS ===")
df['phone_str'] = df['phone'].astype(str)
df['phone_len'] = df['phone_str'].str.len()
print("Phone lengths:", df['phone_len'].value_counts())
# check if valid 10-digit starting with 6,7,8,9
df['phone_valid'] = df['phone_str'].str.match(r'^[6-9]\d{9}$')
print("Phone valid format counts:", df['phone_valid'].value_counts())
print("Invalid phone RTO rate:", (df[~df['phone_valid']]['status_clean'] == 'RTO').mean())
# check repeated digits like 9999999999 or 1234567890
def is_suspicious_phone(p):
    if len(set(p)) <= 2: return True
    if p in ['1234567890', '9876543210']: return True
    return False
df['phone_suspicious'] = df['phone_str'].apply(is_suspicious_phone)
print("Suspicious phone counts:", df['phone_suspicious'].value_counts())
print(df[df['phone_suspicious']][['order_id', 'customer_name', 'phone', 'address', 'status_clean']])

print("\n=== CUSTOMER NAME ANALYSIS ===")
df['name_len'] = df['customer_name'].astype(str).str.len()
df['name_words'] = df['customer_name'].astype(str).apply(lambda x: len(x.split()))
print("Shortest names:")
print(df.sort_values(by='name_len')[['customer_name', 'phone', 'address', 'status_clean']].head(20))

# Suspicious names regex (e.g. test, asdf, single char, digits, dummy)
suspicious_name_pattern = r'(?i)(test|asdf|dummy|fake|qwerty|none|na|abc|xyz|user|admin)'
df['name_suspicious'] = df['customer_name'].astype(str).str.contains(suspicious_name_pattern, regex=True) | (df['name_len'] <= 3) | (df['name_words'] == 1)
print("\nSuspicious name breakdown:")
print(df.groupby('name_suspicious')['status_clean'].value_counts(normalize=True).unstack())
print("Count of suspicious names:", df['name_suspicious'].sum())

print("\n=== ADDRESS ANALYSIS ===")
df['addr_len'] = df['address'].astype(str).str.len()
df['addr_words'] = df['address'].astype(str).apply(lambda x: len(x.split()))
print("Address length percentiles:")
print(df['addr_len'].describe())
print("\nShortest addresses:")
print(df.sort_values(by='addr_len')[['customer_name', 'address', 'city', 'state', 'status_clean']].head(25))

# check RTO rate by address length brackets
df['addr_len_bin'] = pd.cut(df['addr_len'], bins=[0, 15, 25, 40, 60, 100, 500])
print("\nRTO rate by address length bin:")
print(df.groupby('addr_len_bin')['status_clean'].value_counts(normalize=True).unstack())
print("Counts by bin:")
print(df['addr_len_bin'].value_counts().sort_index())

# Check landmark / Hinglish terms in address
hinglish_landmarks = ['ke saamne', 'chowk', 'mandir', 'masjid', 'near', 'opp', 'behind', 'gali', 'road', 'nagar', 'colony', 'flat', 'house', 'plot', 'floor', 'sector', 'block']
for kw in hinglish_landmarks:
    has_kw = df['address'].astype(str).str.contains(kw, case=False, regex=False)
    rto_rate = (df[has_kw]['status_clean'] == 'RTO').mean()
    print(f"Keyword '{kw:12}': count={has_kw.sum():4d}, RTO rate={rto_rate:.1%}")

# Pincode analysis
pincode_stats = df.groupby('pincode')['status_clean'].agg(
    total='count',
    rto=lambda s: (s == 'RTO').sum(),
    rto_rate=lambda s: (s == 'RTO').mean()
)
print("\nPincodes with >= 5 orders and high RTO:")
print(pincode_stats[(pincode_stats['total'] >= 5) & (pincode_stats['rto_rate'] >= 0.5)].sort_values(by='total', ascending=False).head(15))

print("\nPincodes with >= 5 orders and 0 RTO:")
print(pincode_stats[(pincode_stats['total'] >= 5) & (pincode_stats['rto_rate'] == 0)].sort_values(by='total', ascending=False).head(10))

# Order datetime / hour of day
df['order_datetime'] = pd.to_datetime(df['order_datetime'])
df['hour'] = df['order_datetime'].dt.hour
df['dayofweek'] = df['order_datetime'].dt.day_name()
print("\nRTO rate by hour of day:")
hour_stats = df.groupby('hour')['status_clean'].agg(
    total='count',
    rto=lambda s: (s == 'RTO').sum(),
    rto_rate=lambda s: (s == 'RTO').mean()
)
print(hour_stats)

print("\nLate night (23:00 to 05:00) vs Daytime:")
df['is_late_night'] = df['hour'].isin([23, 0, 1, 2, 3, 4, 5])
print(df.groupby('is_late_night')['status_clean'].value_counts(normalize=True).unstack())

# Order value buckets
df['value_bin'] = pd.cut(df['order_value'], bins=[-1, 300, 600, 1000, 1500, 2500, 10000])
print("\nRTO rate by Order Value bin:")
print(df.groupby('value_bin')['status_clean'].value_counts(normalize=True).unstack())
print("Counts by value bin:")
print(df['value_bin'].value_counts().sort_index())

# Courier vs State
print("\nCourier performance in high RTO states (Bihar & UP):")
b_up = df[df['state'].isin(['Bihar', 'Uttar Pradesh'])]
print(b_up.groupby(['state', 'courier'])['status_clean'].agg(
    total='count',
    rto_rate=lambda s: (s == 'RTO').mean()
))

