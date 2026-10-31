# AI Usage Log & Error Correction Audit

In accordance with the assignment guidelines (*"AI tools are allowed, and we encourage them... We hire people who get a lot out of AI"*), this log documents how AI tools were utilized, their specific contributions, and concrete examples where the AI generated incorrect, weak, or misleading suggestions and how they were identified and resolved.

---

### Tools Used & Primary Use Cases

1. **Antigravity / Gemini 3.8 Flash (DeepMind Assistant):**
   * *Tasks:* Exploratory data analysis ideation, rapid scaffolding of Flask and ReportLab PDF structures, designing the multi-language WhatsApp state machine, and drafting the business memorandum.
2. **Scikit-Learn Gradient Boosting & Logistic Regression:**
   * *Tasks:* Baseline feature importance and cross-validation verification of predictive power.

---

### 3 Concrete Examples of Flawed/Weak AI Outputs & How They Were Caught & Fixed

#### Example 1: The "Cancel High-Risk Clusters" Financial Hallucination
* **What the AI Suggested:**  
  When asked to develop an optimal policy to reduce RTO, the AI initially proposed:  
  *"Orders with predicted RTO probability > 50% or customers with 1 prior RTO in Bihar/UP should be automatically cancelled to save warehouse fulfillment and return shipping costs."*
* **Why it was Wrong/Weak:**  
  The AI looked exclusively at the cost of logistics (₹169.40 per RTO) and treated any order with a >50% loss chance as unprofitable. It completely failed to account for the **gross margin (₹402.38)** and **sunk marketing CAC (₹300.00)**.
* **How it was Caught:**  
  We ran a backtest simulation on September 2026 orders (`scripts/simulate_rules.py`). Following the AI's rule to cancel 34 flagged orders avoided 22 returns (saving ₹3,726.80 in logistics), but killed 12 genuine delivered customers (losing ₹7,300.50 gross margin), generating an immediate **Net Rupee Loss of -₹3,573.70**!
* **The Fix:**  
  We derived the mathematical breakeven formula:
  $$p_{\text{breakeven}} = \frac{\text{Gross Profit}}{\text{Gross Profit} + \text{RTO Cost}} = \frac{402.38}{402.38 + 169.40} = 70.36\%$$
  We explicitly overwrote the AI's logic to establish that **no order under 70.4% risk may be cancelled unilaterally**. Instead, they must be routed to the WhatsApp Interception Funnel.

---

#### Example 2: Regex Regex Bias Overlooking Indian Address Deliverability
* **What the AI Suggested:**  
  For address validation, the AI initially wrote a standard Western regex check:  
  `r'^\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Road|Rd|Avenue|Lane|Drive)'`  
  and flagged any address without a formal street suffix as "Invalid / High Risk".
* **Why it was Wrong/Weak:**  
  Indian addresses rarely follow Western street schemas. In our dataset, valid deliveries frequently look like:  
  `"Link chowk se left, SBI Bank ke saamne"` or `"Station Nagar, Opp. Railway Crossing"`.  
  The AI's heuristic misclassified 68% of genuine Indian addresses as "invalid" and would have subjected hundreds of legitimate buyers to unnecessary friction.
* **How it was Caught:**  
  We audited the dataset's address features (`scripts/analyze_data.py`) and found that Hinglish directional keywords like `"ke saamne"`, `"chowk"`, and `"mandir"` appeared in 350+ orders with solid delivery records.
* **The Fix:**  
  We replaced rigid Western regexes with a dedicated Indian D2C semantic analyzer (`engine/llm_verifier.py`). We trained the LLM system prompt and heuristic parser to identify Indian landmarks (`chowk`, `mandir`, `gali`, `opp`, `ke saamne`) and award deliverability credit even when formal house numbers are missing.

---

#### Example 3: Windows Console UTF-8 Rupee Character Crash
* **What the AI Suggested:**  
  In `cli.py`, the AI generated formatted summary strings using Unicode currency symbols:  
  `print(f"Gross Logistics Cash Saved: ₹{fin['gross_rto_savings']:,.2f}")`
* **Why it was Wrong/Weak:**  
  When executed on a standard Windows PowerShell environment (which defaults to `cp1252` encoding), the code crashed immediately with:  
  `UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9' in position 30: character maps to <undefined>`.  
  A candidate submitting this would have failed the 10-minute setup test on any Windows machine.
* **How it was Caught:**  
  Caught during terminal testing of the CLI tool (`python cli.py stats --month 2026-09`).
* **The Fix:**  
  Added a defensive encoding reconfigurator at the entry point of `cli.py`:
  ```python
  if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
      try:
          sys.stdout.reconfigure(encoding='utf-8')
      except Exception:
          pass
  ```
  ensuring seamless multi-platform execution across Windows, macOS, and Linux.
