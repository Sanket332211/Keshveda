# Engineering & Product Decision Log

This document provides a chronological record of the key architectural, financial, and modeling decisions made while building the Keshveda COD AI Decision Engine.

---

### Decision 1: Interception Funnel vs. Unilateral Cancellation
* **Context:** The Head of Operations wanted any risky COD order or bad pincode cancelled immediately.
* **Alternative Considered:** Hard-coded rule engine automatically cancelling orders with risk score >60 or in high-RTO states (Bihar, UP).
* **Why Rejected:** 
  * Financial math proved that cancelling a genuine customer destroys **₹702.38** (gross margin + CAC), which is **4.15x more expensive than an RTO (₹169.40)**.
  * In the data, 32.2% of orders with ultra-short addresses (<=5 chars) and 65.6% of orders in Bihar/UP under ₹800 were successfully delivered.
* **Choice Made:** Built a **4-bucket triage model**. Hard cancellation is restricted strictly to blatant fakes (e.g. `.` address + `asdf` name) and chronic repeat offenders (prior RTO >= 2). All other at-risk orders are routed through an **automated WhatsApp Interception Funnel** (address confirmation or prepaid discount nudge).

---

### Decision 2: LLM Boundary — Where to Use AI vs. Deterministic Code
* **Context:** The assignment explicitly required: *"Use an LLM where it actually helps... Do not use an LLM for things simple code or maths can do better. Tell us where you drew that line and why."*
* **Alternative Considered:** Feeding the entire order row as a prompt to an LLM to output risk probability and decision directly.
* **Why Rejected:** 
  * LLMs are slow (500–2,000ms latency), expensive, non-deterministic, and prone to hallucinating mathematical sums or threshold logic.
  * Pincode mapping, prior RTO counts, and ticket-size thresholds are discrete, mathematical facts better handled by sub-millisecond code.
* **Choice Made:** 
  * **Code / Math handles:** Numeric feature extraction, customer history aggregation, strict threshold enforcement, financial simulation, and timer expirations.
  * **LLM handles:** Unstructured text comprehension—detecting whether an Indian address has sufficient landmarks and premise numbers, resolving Hinglish directions ("Link chowk se left, SBI Bank ke saamne"), spotting subtle fake names, and parsing natural language customer intent in WhatsApp chat.

---

### Decision 3: Resilience Architecture & Zero-Dependency Reviewer Experience
* **Context:** Reviewers running take-home assignments often lack specific proprietary API keys (e.g., Gemini API key or OpenAI key), which causes crashes.
* **Alternative Considered:** Requiring `GEMINI_API_KEY` in environment variables before the app can boot.
* **Why Rejected:** Fails the core requirement: *"README that lets us run it in under 10 minutes"*.
* **Choice Made:** Implemented a **dual-mode LLM engine** in `engine/llm_verifier.py`.
  * If `GEMINI_API_KEY` is present, it calls Google Gemini 2.5 Flash with structured JSON output.
  * If no API key is provided, it seamlessly falls back to a high-fidelity local semantic parser that reproduces identical schema outputs. The reviewer can clone and run the full stack out-of-the-box with zero API blockers.

---

### Decision 4: Prepaid Nudge Economics — Determining the ₹50 Discount
* **Context:** How much discount should we offer to convert a COD customer to prepaid, and why that number?
* **Alternatives Considered:** 
  * 15% discount (~₹97 on ₹649 AOV): Eats up all gross logistics savings, resulting in net negative cash per conversion.
  * 5% discount (~₹32): Too small in Indian D2C psychology to overcome buyer inertia to pull out a UPI app.
* **Choice Made:** Selected **FLAT ₹50 OFF** (or ~8% of ₹649 AOV).
  * **Mathematical Proof:** In high-risk cohorts, COD RTO is 45% (expected loss = ₹76.23). Prepaid RTO is 4% (expected loss = ₹6.78). Gross logistics savings = **₹69.45**.
  * By offering ₹50, the company retains **+₹19.45 net cash profit** per conversion while converting an uncommitted shopper into a guaranteed paid delivery and securing customer acquisition.

---

### Decision 5: User Interface Architecture — Flask SPA with Tailwind & Chart.js
* **Context:** The founder needs one screen to review daily operations, inspect orders, and simulate WhatsApp conversations.
* **Alternative Considered:** Streamlit or Jupyter Notebook.
* **Why Rejected:** Streamlit re-executes Python scripts on every interaction, making complex multi-turn WhatsApp simulators clumsy and stateful chats slow.
* **Choice Made:** Built a single lightweight Flask application (`app.py`) serving an interactive Single Page Application (Tailwind CSS + Chart.js). It includes:
  * 4 executive KPI cards answering the founder's morning questions.
  * Dynamic Chart.js financial and regional breakdowns.
  * A real-time, interactive WhatsApp simulator with Hinglish/English toggles, quick replies, and timer simulations.
  * A non-technical threshold slider modal that updates `config/thresholds.json` and recalculates simulation numbers live.

---

### Decision 6: WhatsApp Flow Timing — T+5 Minutes Outbound
* **Context:** When should the confirmation message be sent?
* **Alternatives Considered:**
  * Instant (T+0s): Customer is still on the thank-you page; triggers message fatigue and feels intrusive.
  * T+2 Hours: Customer has exited the shopping headspace and may have ordered from a competitor.
* **Choice Made:** **T+5 Minutes**.
  * Gives the customer time to review their order confirmation email/SMS.
  * Catches impulse shoppers while intent is still warm.
  * Provides enough runway for 12-hour reminder and 24-hour auto-cancellation before the warehouse packing shift ends.

