"""
Command Line Interface (CLI) for COD Decision Engine
Allows evaluating single orders, processing batch CSV files, and computing financial simulations.
"""

import argparse
import json
import sys
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from engine.decision_engine import DecisionEngine


def main():
    parser = argparse.ArgumentParser(description="Keshveda COD AI Decision Engine CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a single order JSON")
    eval_parser.add_argument("--order", type=str, required=True, help="Order JSON string or file path")
    eval_parser.add_argument("--config", type=str, default="config/thresholds.json", help="Path to config file")

    # Command: batch
    batch_parser = subparsers.add_parser("batch", help="Evaluate a batch CSV file")
    batch_parser.add_argument("--csv", type=str, required=True, help="Input CSV file path")
    batch_parser.add_argument("--output", type=str, default="evaluated_orders.csv", help="Output annotated CSV path")
    batch_parser.add_argument("--config", type=str, default="config/thresholds.json", help="Path to config file")

    # Command: stats
    stats_parser = subparsers.add_parser("stats", help="Show financial simulation and baseline comparison")
    stats_parser.add_argument("--csv", type=str, default="orders_sample.csv", help="Path to CSV dataset")
    stats_parser.add_argument("--month", type=str, default="2026-09", help="Month filter (YYYY-MM or 'all')")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = DecisionEngine(config_path=args.config if hasattr(args, 'config') else "config/thresholds.json")

    if args.command == "evaluate":
        try:
            if args.order.startswith("{"):
                order_data = json.loads(args.order)
            else:
                with open(args.order, "r", encoding="utf-8") as f:
                    order_data = json.load(f)
        except Exception as e:
            print(f"Error parsing order JSON: {e}")
            sys.exit(1)

        result = engine.evaluate_order(order_data)
        print("\n" + "="*50)
        print(f" ORDER EVALUATION: {result['order_id']}")
        print("="*50)
        print(f" ACTION:        {result['action'].upper()}")
        print(f" RISK SCORE:    {result['risk_score']}/100")
        print(f" REASON:        {result['reason']}")
        print(f" TRIGGERS:      {', '.join(result['triggers']) if result['triggers'] else 'None'}")
        print("\n LLM DELIVERABILITY ASSESSMENT:")
        print(f" {result['llm_analysis']['deliverability_assessment']}")
        print(f" Address Score: {result['llm_analysis']['address_quality_score']}/100")
        print(f" Has House/Flat: {result['llm_analysis']['has_house_or_flat']}")
        print(f" Has Landmark:   {result['llm_analysis']['has_landmark']}")
        print("="*50 + "\n")

    elif args.command == "batch":
        print(f"Reading {args.csv}...")
        df = pd.read_csv(args.csv)
        print(f"Evaluating {len(df)} orders...")
        annotated_df, simulation = engine.evaluate_batch(df)
        annotated_df.to_csv(args.output, index=False)
        print(f"\nSaved annotated orders to {args.output}")
        print("\n=== SUMMARY ACTION BUCKETS ===")
        for b, count in simulation.get("buckets", {}).items():
            print(f"  {b:25}: {count:5d} ({count/len(df):.1%})")
        fin = simulation.get("financial_impact_rupees", {})
        print(f"\nNet Rupee Gain: ₹{fin.get('net_rupee_gain', 0):,.2f}")

    elif args.command == "stats":
        df = pd.read_csv(args.csv)
        df['order_datetime'] = pd.to_datetime(df['order_datetime'])
        if args.month != "all":
            df = df[df['order_datetime'].dt.to_period('M') == args.month]
            print(f"\n--- FINANCIAL SIMULATION: {args.month} ({len(df)} orders) ---")
        else:
            print(f"\n--- FINANCIAL SIMULATION: ALL DATA ({len(df)} orders) ---")

        _, simulation = engine.evaluate_batch(df)
        base = simulation["baseline"]
        fin = simulation["financial_impact_rupees"]
        metrics = simulation["intervention_metrics"]

        print(f"Baseline RTO Rate:            {base['rto_rate_pct']}% ({base['rto']} RTOs)")
        print(f"Projected Post-Engine RTO:    {metrics['new_projected_rto_rate_pct']}%")
        print(f"RTOs Avoided:                 {metrics['avoided_rto_count']:.1f} ({metrics['rto_reduction_pct']}%)")
        print(f"Gross Logistics Cash Saved:   ₹{fin['gross_rto_savings']:,.2f}")
        print(f"False Cancellation Loss:      ₹{fin['lost_margin_from_false_cancellations_and_dropoffs']:,.2f}")
        print(f"Prepaid Discounts Paid:       ₹{fin['prepaid_discounts_incurred']:,.2f}")
        print(f"NET PROFIT GAIN:              ₹{fin['net_rupee_gain']:,.2f}")


if __name__ == "__main__":
    main()
