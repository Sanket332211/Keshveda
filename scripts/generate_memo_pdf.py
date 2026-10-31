"""
Generates an executive-styled PDF of the Business Memo using ReportLab.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf(output_filename="BUSINESS_MEMO.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#059669")
    )
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569")
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=6,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )
    table_cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # Header / Meta
    story.append(Paragraph("KESHVEDA · EXECUTIVE MEMORANDUM", subtitle_style))
    story.append(Paragraph("Strategic COD Risk Interception: Balancing Growth vs. RTO", title_style))
    story.append(Spacer(1, 4))
    
    memo_meta = [
        [Paragraph("<b>TO:</b> Founder & CEO, Keshveda", meta_style), Paragraph("<b>DATE:</b> October 31, 2026", meta_style)],
        [Paragraph("<b>FROM:</b> AI Automation & Decision Systems Team", meta_style), Paragraph("<b>SUBJECT:</b> Maximizing Net Profit via AI COD Interception", meta_style)]
    ]
    meta_table = Table(memo_meta, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceBefore=2, spaceAfter=6))

    # Executive Summary Callout
    exec_summary_text = (
        "<b>Executive Summary:</b> Operations wants to cancel risky COD orders to stop ₹169.40 RTO losses. "
        "Marketing wants to protect sales and ₹300+ Meta ad CAC. "
        "<b>The Math:</b> Falsely cancelling a genuine customer loses ₹402.38 gross margin + ₹300 CAC = <b>₹702.38</b>, "
        "which is <b>4.15x more expensive than an RTO</b>. "
        "Our AI Decision Engine reconciles both by deploying an interactive WhatsApp Interception Funnel. "
        "On September 2026 orders, it <b>reduced RTO from 26.0% to 12.2% (-53%)</b>, saved <b>₹7,825.43 in logistics cash</b>, "
        "and generated <b>+₹2,649.01 in Net Profit Gain</b> on the sample (+₹13,500/month scaled)."
    )
    callout_data = [[Paragraph(exec_summary_text, callout_style)]]
    callout_table = Table(callout_data, colWidths=[540])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86efac")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 6))

    # Section 1
    story.append(Paragraph("1. Surprising Findings in Our Data (with Exact Numbers)", h1_style))
    story.append(Paragraph(
        "<b>• The Address Blindspot:</b> 115 orders had addresses &le;5 characters (e.g. '.', 'xyz', 'home'). "
        "While their RTO rate was high (67.8%), <b>32.2% were successfully delivered</b>! Delivery riders called the customer in the locality. "
        "Blindly cancelling every short address would have flushed 37 genuine customers and ₹11,100 in Meta ad CAC down the drain.<br/>"
        "<b>• The False Cancellation Trap:</b> In September 2026, 34 orders triggered high risk. Cancelling all 34 would have avoided 22 returns (saving ₹3,726.80), "
        "but falsely killed 12 genuine sales (losing ₹7,300.50 margin), producing a <b>Net Loss of -₹3,573.70</b>! Blanket cancellations destroy cash.<br/>"
        "<b>• Geographic Skew Driven by Order Value:</b> Coastal/metro states showed low RTO (Maharashtra: 17.7%, TN: 20.3%), while Bihar (53.4%) "
        "and UP (44.7%) had severe returns—heavily concentrated in orders &gt;₹1,500. Orders &lt;₹800 in Bihar still delivered at a 68% rate.<br/>"
        "<b>• Data Hygiene:</b> 30 exact duplicate order pairs (60 rows) exist in Shopify exports, risking double-fulfillment and artificial RTOs.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 2
    story.append(Paragraph("2. Recommended Decision Rules & September 2026 Impact", h1_style))
    story.append(Paragraph(
        "We segment incoming COD orders into 4 automated actions: <b>Ship As-Is</b> (clean history/address), "
        "<b>Ship After Confirmation</b> (incomplete address/prior RTO=1), <b>Nudge to Prepaid</b> (&gt;₹1,500 or &gt;₹800 in Bihar/UP with ₹50 discount), "
        "and <b>Hold / Cancel</b> (only for blatant fakes and chronic RTO &ge;2 offenders).",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Simulation Table
    sim_data = [
        [Paragraph("Metric", table_cell_header), Paragraph("Baseline (Status Quo)", table_cell_header), Paragraph("With AI Decision Engine", table_cell_header), Paragraph("Variance / Benefit", table_cell_header)],
        [Paragraph("Total COD Orders Evaluated", table_cell_style), Paragraph("334", table_cell_style), Paragraph("334", table_cell_style), Paragraph("—", table_cell_style)],
        [Paragraph("Orders Shipped As-Is", table_cell_style), Paragraph("334 (100%)", table_cell_style), Paragraph("155 (46.4%)", table_cell_style), Paragraph("Frictionless dispatch", table_cell_style)],
        [Paragraph("Orders Held for Confirmation", table_cell_style), Paragraph("0", table_cell_style), Paragraph("88 (26.3%)", table_cell_style), Paragraph("Verified on WhatsApp", table_cell_style)],
        [Paragraph("Orders Nudged to Prepaid", table_cell_style), Paragraph("0", table_cell_style), Paragraph("57 (17.1%)", table_cell_style), Paragraph("14.3 converted via ₹50 off", table_cell_style)],
        [Paragraph("Orders Cancelled / Held", table_cell_style), Paragraph("0", table_cell_style), Paragraph("34 (10.2%)", table_cell_style), Paragraph("22 guaranteed RTOs stopped", table_cell_style)],
        [Paragraph("Total RTO Returns", table_cell_bold), Paragraph("87 (26.0%)", table_cell_bold), Paragraph("40.8 (12.2%)", table_cell_bold), Paragraph("-46.2 RTOs (-53.1%)", table_cell_bold)],
        [Paragraph("Gross Logistics RTO Cost", table_cell_style), Paragraph("₹14,737.80", table_cell_style), Paragraph("₹6,912.37", table_cell_style), Paragraph("+₹7,825.43 Saved", table_cell_bold)],
        [Paragraph("Prepaid Discounts Given", table_cell_style), Paragraph("₹0.00", table_cell_style), Paragraph("₹787.50", table_cell_style), Paragraph("-₹787.50 (Invested)", table_cell_style)],
        [Paragraph("NET REALIZED CONTRIBUTION", table_cell_bold), Paragraph("₹118,890.80", table_cell_bold), Paragraph("₹121,539.81", table_cell_bold), Paragraph("+₹2,649.01 NET GAIN", table_cell_bold)]
    ]
    sim_table = Table(sim_data, colWidths=[160, 120, 130, 130])
    sim_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(sim_table)
    story.append(Spacer(1, 6))

    # Section 3
    story.append(Paragraph("3. Balancing Operations vs. Marketing in Rupees (₹)", h1_style))
    story.append(Paragraph(
        "<b>• The 4.15x Trade-off Ratio:</b> RTO loss = ₹65 + ₹65 + ₹25 + (8% &times; ₹180) = <b>₹169.40</b>. "
        "False cancellation loss = ₹402.38 margin + ₹300 CAC = <b>₹702.38</b>. Ratio = <b>4.15x</b>. "
        "Cancelling one good customer wipes out the logistics savings of four prevented RTOs.<br/>"
        "<b>• Breakeven Risk Threshold (70.4%):</b> (1 - p)&times;402.38 - p&times;169.40 = 0 &rArr; p = <b>70.36%</b>. "
        "Unless RTO risk exceeds 70.4%, shipping the order produces positive expected cash value.<br/>"
        "<b>• The ₹50 Prepaid Nudge Math:</b> In high-risk cohorts, COD RTO is 45% (₹76.23 expected loss). "
        "Prepaid RTO is 4% (₹6.78 expected loss). Switching to prepaid saves ₹69.45. "
        "Giving ₹50 discount leaves <b>+₹19.45 net cash profit per conversion</b> while securing customer acquisition.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 4
    story.append(Paragraph("4. Failure Modes & Early Warning Signals", h1_style))
    story.append(Paragraph(
        "<b>1. WhatsApp Spam Flags:</b> Track WhatsApp Business API Quality Score. If it drops to Yellow, rate-limit pings to T+5m and add instant opt-out.<br/>"
        "<b>2. Confirmation Drop-off:</b> Monitor reply rates (target &gt;80%). If replies fall below 75%, trigger fallback SMS at T+6h.<br/>"
        "<b>3. Courier Fake NDR Fraud:</b> Delivery boys faking 'Customer Unavailable'. Trigger automated WhatsApp NDR verification when courier logs a failure.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 5
    story.append(Paragraph("5. Roadmap: What to Build in Next 2 Weeks", h1_style))
    story.append(Paragraph(
        "<b>• Shopify Webhook App (Week 1):</b> Direct webhook integration tagging orders in Shopify ERP within 5 seconds of checkout.<br/>"
        "<b>• Automated NDR Re-Attempt Engine (Week 2):</b> Real-time courier callback listening to rescue in-transit failed deliveries.<br/>"
        "<b>• Checkout Autocomplete (Week 2):</b> Google Places address autocomplete at checkout to fix premise numbers before order placement.",
        body_style
    ))

    doc.build(story)
    print(f"Successfully generated {output_filename}")

if __name__ == "__main__":
    generate_pdf()

