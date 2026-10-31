import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, precision_recall_curve, classification_report
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

df = pd.read_csv('orders_sample.csv')
# drop duplicates or keep?
# Let's inspect with and without duplicates
df_clean = df.drop_duplicates().copy()
df_clean['status_clean'] = df_clean['final_status'].astype(str).str.strip().str.upper()
# filter out IN_TRANSIT
df_clean = df_clean[df_clean['status_clean'].isin(['DELIVERED', 'RTO'])].copy()
df_clean['target'] = (df_clean['status_clean'] == 'RTO').astype(int)

# Feature engineering
# 1. Address features
fake_name_list = {'test', 'asdf', 'na', 'aaa', 'abc', 'test order', 'qwerty', 'dummy', 'fake'}
df_clean['is_fake_name'] = df_clean['customer_name'].astype(str).str.lower().str.strip().isin(fake_name_list).astype(int)
df_clean['name_words'] = df_clean['customer_name'].astype(str).apply(lambda x: len(x.split()))
df_clean['addr_len'] = df_clean['address'].astype(str).str.len()
df_clean['is_short_addr'] = (df_clean['addr_len'] <= 15).astype(int)
df_clean['has_house_num'] = df_clean['address'].astype(str).str.contains(r'\d+', regex=True).astype(int)

# 2. State risk
state_rto_rate = df_clean.groupby('state')['target'].transform('mean')
df_clean['state_rto_rate'] = state_rto_rate
df_clean['is_high_risk_state'] = df_clean['state'].isin(['Bihar', 'Uttar Pradesh', 'Madhya Pradesh']).astype(int)

# 3. Customer history
df_clean['prior_rto_ge1'] = (df_clean['customer_prior_rto'] >= 1).astype(int)
df_clean['prior_rto_ge2'] = (df_clean['customer_prior_rto'] >= 2).astype(int)
df_clean['is_repeat_clean'] = ((df_clean['customer_prior_orders'] > 0) & (df_clean['customer_prior_rto'] == 0)).astype(int)

# 4. Order value
df_clean['is_high_value'] = (df_clean['order_value'] > 1500).astype(int)
df_clean['is_very_high_value'] = (df_clean['order_value'] > 2500).astype(int)

# 5. Phone valid
df_clean['phone_invalid'] = (~df_clean['phone'].astype(str).str.match(r'^[6-9]\d{9}$')).astype(int)

features = [
    'customer_prior_orders', 'customer_prior_rto', 'order_value', 'num_items',
    'is_fake_name', 'name_words', 'addr_len', 'is_short_addr', 'has_house_num',
    'state_rto_rate', 'is_high_risk_state', 'prior_rto_ge1', 'prior_rto_ge2',
    'is_repeat_clean', 'is_high_value', 'phone_invalid'
]

X = df_clean[features].fillna(0)
y = df_clean['target']

rf = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
preds_prob = cross_val_predict(rf, X, y, cv=cv, method='predict_proba')[:, 1]

auc = roc_auc_score(y, preds_prob)
print(f"5-Fold CV ROC AUC: {auc:.4f}")

rf.fit(X, y)
feat_imp = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
print("\nFeature Importances:")
print(feat_imp)
