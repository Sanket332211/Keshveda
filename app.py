"""
Flask Application: Founder Morning Dashboard & WhatsApp Simulator
Provides REST APIs for:
- Batch Order Evaluation & Metric Summary
- Threshold Adjustment & Live Re-simulation
- WhatsApp Flow Simulation
"""

import os
import json
from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request, jsonify

from engine.decision_engine import DecisionEngine
from whatsapp.flow_manager import FlowManager

app = Flask(__name__)
engine = DecisionEngine(config_path="config/thresholds.json")
whatsapp_manager = FlowManager()

# Global in-memory cache for loaded orders and sessions
DATA_FILE = "orders_sample.csv"
_orders_df = None
_sessions = {}  # order_id -> session_dict


def get_data() -> pd.DataFrame:
    global _orders_df
    if _orders_df is None:
        df = pd.read_csv(DATA_FILE)
        df['order_datetime'] = pd.to_datetime(df['order_datetime'])
        _orders_df = df
    return _orders_df


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary", methods=["GET"])
def api_summary():
    """
    Returns the morning dashboard metrics:
    - 4 bucket counts
    - Estimated ₹ saved from avoided RTOs
    - Estimated ₹ lost from cancelled orders that might have been genuine
    - Net ₹ impact
    - Date filtering (yesterday, last month, all)
    """
    df = get_data().copy()
    time_filter = request.args.get("time_filter", "last_month")

    if time_filter == "yesterday":
        # In this dataset, maximum date is 2026-09-30, so yesterday is the latest date
        latest_date = df['order_datetime'].dt.date.max()
        df_filtered = df[df['order_datetime'].dt.date == latest_date].copy()
    elif time_filter == "last_month":
        # September 2026
        df_filtered = df[df['order_datetime'].dt.to_period('M') == '2026-09'].copy()
    else:
        df_filtered = df.copy()

    annotated_df, simulation = engine.evaluate_batch(df_filtered)

    # Format orders for table (limit 150 for quick rendering, searchable on frontend)
    records = []
    for _, row in annotated_df.head(150).iterrows():
        records.append({
            "order_id": row.get("order_id"),
            "order_datetime": str(row.get("order_datetime")),
            "customer_name": row.get("customer_name"),
            "phone": str(row.get("phone")),
            "address": row.get("address"),
            "city": row.get("city"),
            "state": row.get("state"),
            "pincode": str(row.get("pincode")).replace(".0", ""),
            "order_value": int(row.get("order_value", 0)),
            "items": row.get("items"),
            "action": row.get("action"),
            "risk_score": int(row.get("risk_score", 0)),
            "reason": row.get("reason"),
            "actual_status": row.get("final_status")
        })

    # State RTO distribution
    state_breakdown = df_filtered.groupby('state').agg(
        total=('order_id', 'count'),
        rto=('final_status', lambda s: (s.astype(str).str.strip().str.upper() == 'RTO').sum())
    ).reset_index()
    state_breakdown['rto_rate'] = (state_breakdown['rto'] / state_breakdown['total'] * 100).round(1)
    state_breakdown = state_breakdown.sort_values(by='total', ascending=False).head(8).to_dict(orient='records')

    return jsonify({
        "time_filter": time_filter,
        "total_evaluated": len(df_filtered),
        "simulation": simulation,
        "sample_orders": records,
        "state_breakdown": state_breakdown,
        "current_thresholds": engine.thresholds
    })


@app.route("/api/evaluate_order", methods=["POST"])
def api_evaluate_single():
    """Evaluates an arbitrary single order payload in real-time."""
    payload = request.json or {}
    result = engine.evaluate_order(payload)
    return jsonify(result)


@app.route("/api/update_thresholds", methods=["POST"])
def api_update_thresholds():
    """Updates operational thresholds and saves them to config/thresholds.json."""
    new_thresholds = request.json or {}
    engine.thresholds = new_thresholds
    engine.reload_config()

    with open("config/thresholds.json", "w", encoding="utf-8") as f:
        json.dump(new_thresholds, f, indent=2)

    return jsonify({"status": "success", "message": "Thresholds updated and saved successfully!"})


@app.route("/api/whatsapp/start", methods=["POST"])
def api_whatsapp_start():
    """Starts or resets a WhatsApp session for a specific order."""
    payload = request.json or {}
    order_id = payload.get("order_id")
    lang = payload.get("lang", "hinglish")

    df = get_data()
    order_rows = df[df["order_id"] == order_id]
    if order_rows.empty:
        # Fallback to sample or provided payload
        order_dict = payload
    else:
        order_dict = order_rows.iloc[0].to_dict()

    eval_res = engine.evaluate_order(order_dict)
    session = whatsapp_manager.create_session(order_dict, action=eval_res["action"], lang=lang)
    _sessions[order_id] = session

    return jsonify({"session": session, "evaluation": eval_res})


@app.route("/api/whatsapp/message", methods=["POST"])
def api_whatsapp_message():
    """Processes an incoming reply from the customer in the WhatsApp chat simulator."""
    payload = request.json or {}
    order_id = payload.get("order_id")
    user_text = payload.get("text", "")

    if order_id not in _sessions:
        return jsonify({"error": "Session not found. Please start a session first."}), 404

    session = _sessions[order_id]
    updated_session = whatsapp_manager.process_incoming_message(session, user_text)
    _sessions[order_id] = updated_session

    return jsonify({"session": updated_session})


@app.route("/api/whatsapp/timer", methods=["POST"])
def api_whatsapp_timer():
    """Simulates a background timer event: '12h_reminder' or '24h_auto_cancel'."""
    payload = request.json or {}
    order_id = payload.get("order_id")
    event_type = payload.get("event", "12h_reminder")

    if order_id not in _sessions:
        return jsonify({"error": "Session not found."}), 404

    session = _sessions[order_id]
    updated_session = whatsapp_manager.trigger_timer_event(session, event_type)
    _sessions[order_id] = updated_session

    return jsonify({"session": updated_session})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

