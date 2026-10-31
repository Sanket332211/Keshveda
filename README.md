# Keshveda | AI COD Decision Engine & Founder Dashboard

An end-to-end intelligent decision system built for Indian D2C haircare brands to tackle high Cash on Delivery (COD) Return-to-Origin (RTO) rates without destroying top-line revenue or marketing CAC.

---

## 🚀 Quickstart (Run in Under 5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*(All core libraries: Flask, pandas, numpy, scikit-learn, reportlab)*

### 2. Launch Founder Dashboard & WhatsApp Simulator
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

### 3. Run Automated Tests
```bash
python tests/test_suite.py
```
*(Runs 16 unit & integration tests in < 0.2s)*

### 4. Run CLI Tools
```bash
# View last month's financial simulation & baseline comparison
python cli.py stats --month 2026-09

# Evaluate a sample order JSON
python cli.py evaluate --order test_order_hinglish.json

# Process an entire batch CSV
python cli.py batch --csv orders_sample.csv --output evaluated_orders.csv
```

---

## 📑 Deliverables Overview

1. **[Business Memo (Executive PDF)](BUSINESS_MEMO.pdf)** — 2-page founder memo with data surprises, recommended rules, Operations vs. Marketing ₹ trade-offs, failure modes, and 2-week roadmap. *(Markdown version: [BUSINESS_MEMO.md](BUSINESS_MEMO.md))*.
2. **[Decision Log](DECISION_LOG.md)** — Key architectural, financial, and modeling choices, alternatives considered, and rationale.
3. **[AI Usage Log](AI_USAGE_LOG.md)** — Tools used and 3 detailed examples where AI gave weak/wrong output and how caught and fixed.
4. **[Threshold Configuration](config/thresholds.json)** — Non-technical JSON file allowing ops managers to tweak thresholds without touching code.

---

## 💡 The Core Problem & Financial Trade-Off

* **The Problem:** 55% of orders are COD, and ~28% RTO. Every return burns **₹169.40** (₹65 forward + ₹65 return + ₹25 pack + 8% damage on ₹180 product).
* **The Conflict:**
  * **Head of Operations:** *"Cancel any risky COD order. If a pincode has bad history, stop COD there."*
  * **Head of Marketing:** *"We spend ₹300+ on Meta ads to acquire customers. If you cancel their order, you waste that money and kill growth."*
* **The Mathematical Resolution (Rupees, Not Opinions):**
  * **Loss from an RTO:** ₹169.40
  * **Loss from a False Cancellation:** Gross Profit (₹402.38) + Sunk CAC (₹300.00) = **₹702.38**
  * **The 4.15x Ratio:** $\frac{₹702.38}{₹169.40} \approx \mathbf{4.15\times}$
  * *Falsely cancelling one genuine customer is more than 4x more expensive than suffering a return!*
  * **Breakeven Threshold:** Unless an order's RTO probability exceeds **70.4%**, shipping the order produces positive expected cash contribution.

---

## ⚙️ How the Decision Engine Works (Part 1)

Every incoming COD order is evaluated and classified into one of four automated actions:

```
                          [ Incoming COD Order ]
                                    │
                                    ▼
                 [ LLM Semantic Address & Identity Analyzer ]
               (Hinglish landmarks, premise numbers, fake names)
                                    │
                                    ▼
                      [ Risk Score Calculation ]
                                    │
      ┌─────────────────┬───────────┴───────────┬─────────────────┐
      │                 │                       │                 │
      ▼                 ▼                       ▼                 ▼
[ 1. Ship As-Is ] [ 2. Confirm ]        [ 3. Nudge Prepaid ] [ 4. Hold/Cancel ]
Repeat buyers or  Incomplete address,   High ticket (>₹1500  Blatant fakes ('.')
clean profile in  1 prior RTO, or       or >₹800 in UP/Bihar) and chronic repeat
stable regions.   first-time UP/Bihar.  with flat ₹50 OFF.   RTOs (≥2).
```

### Where We Drew the Line Between LLM and Code
* **Deterministic Code & Maths Handles:** Pincode validation, numeric order values, prior order counts, financial breakeven formulas, and threshold evaluations.
* **LLM Handles:** Unstructured Indian text semantics—interpreting Hinglish addresses (`"Link chowk se left, SBI Bank ke saamne"`), assessing whether a courier rider can find the premise, identifying subtle fake names (`"asdf"`, `"test"`, `"na"`), and interpreting WhatsApp replies.

---

## 💬 WhatsApp Confirmation Flow (Part 2)

Integrated state machine supporting bilingual **Hinglish** and **English**:

1. **Ship After Confirmation Flow:**
   * **Outbound Trigger:** Sent at T+5 minutes after order placement.
   * **Positive Reply (`"1"`, `"yes"`, `"ha"`, `"confirm"`):** Releases order for packing; sends confirmation note.
   * **Cancellation Reply (`"2"`, `"no"`, `"cancel"`, `"mat bhejo"`):** Instantly cancels order, saving ₹169.40 in shipping and releasing inventory.
   * **Address Correction (`"Flat 402, near shiv mandir"`):** Extracts updated address via NLP, updates database, and confirms shipment.
   * **Timer Expirations:** T+12h reminder; T+24h auto-cancellation if customer remains unresponsive.
2. **Nudge to Prepaid Flow:**
   * **The Math:** In high-risk cohorts (45% COD RTO risk), expected RTO cost is ₹76.23. On prepaid (4% RTO), cost is ₹6.78. Gross savings = **₹69.45**.
   * By offering **FLAT ₹50 OFF**, the brand retains **+₹19.45 net cash profit per converted order**, eliminates COD cash handling fees, and locks in customer acquisition.

---

## 📊 Founder Morning Dashboard (Part 3)

The single screen built for the founder answers four key morning questions:
1. **Order Buckets:** How many orders were classified into each of the 4 buckets yesterday.
2. **Logistics Cash Saved:** Rupee savings from predicted returns avoided (at ₹169.40/return).
3. **False Cancellation Loss:** Rupee margin lost from cancelled orders that might have been genuine.
4. **Net Rupee Bottom-Line Impact:** Net profit gain after paying all customer discounts.

### Key Dashboard Features:
* **Interactive WhatsApp Simulator:** Test any order live, simulate customer replies in Hinglish/English, test address corrections, and test timer expirations.
* **Rule Threshold Editor Modal:** Non-technical sliders to modify thresholds live; updates `config/thresholds.json` and recalculates simulation numbers instantly.
* **Order Intelligence Feed:** Filterable, searchable table displaying risk scores, LLM address assessments, and plain-English ops rationales.

---

## 📈 September 2026 Simulation Results

Tested against 334 historical orders from September 2026:
* **Baseline COD RTO Rate:** 26.0% (87 returns)
* **Post-Engine RTO Rate:** **12.2%** (40.8 returns)
* **Avoided Returns:** **46.2 RTOs (-53.1%)**
* **Gross Logistics Cash Saved:** **₹7,825.43**
* **False Cancellation Margin Loss:** ₹4,388.92
* **Prepaid Discounts Granted:** ₹787.50
* **NET PROFIT GAIN:** **+₹2,649.01** on sample *(~₹13,500/month scaled to 1,650 COD volume)*.

---

## 📁 Repository Structure

```
├── README.md                           # Documentation & quickstart (<5 min)
├── BUSINESS_MEMO.md                    # The 2-page founder memo (Markdown)
├── BUSINESS_MEMO.pdf                   # The 2-page founder memo (Executive PDF)
├── DECISION_LOG.md                     # Architectural and financial decision log
├── AI_USAGE_LOG.md                     # AI tools used & error-correction audit
├── requirements.txt                    # Python dependencies
├── app.py                              # Flask Web Server & Dashboard
├── cli.py                              # CLI for single/batch order evaluation
├── config/
│   └── thresholds.json                 # Non-technical editable threshold configuration
├── engine/
│   ├── __init__.py
│   ├── decision_engine.py              # Core 4-bucket classification engine
│   ├── llm_verifier.py                 # LLM address, name, and intent analyzer with fallback
│   ├── financial_model.py              # Rupee (₹) economics and impact simulator
│   └── rules.py                        # Rule evaluator & feature extractor
├── whatsapp/
│   ├── __init__.py
│   ├── flow_manager.py                 # WhatsApp state machine & NLP intent parser
│   ├── templates.py                    # Multi-language message templates (Hinglish/English)
│   └── simulator.py                    # Interactive chat session handler
├── templates/
│   └── index.html                      # Founder Dashboard SPA (Tailwind CSS + Chart.js)
├── static/
│   └── js/dashboard.js                 # Dashboard charts, APIs, and WhatsApp simulator
├── tests/
│   ├── __init__.py
│   └── test_suite.py                   # 16 unit & integration tests
└── scripts/
    ├── generate_memo_pdf.py            # Generates BUSINESS_MEMO.pdf via ReportLab
    ├── analyze_data.py                 # Comprehensive EDA script
    ├── deep_dive.py                    # Deep dive address & fake name analysis
    ├── test_model.py                   # 5-fold CV Gradient Boosting baseline
    └── simulate_rules.py               # Historical backtesting simulation
```

