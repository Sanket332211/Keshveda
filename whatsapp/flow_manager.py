"""
WhatsApp Conversation Flow Manager & State Machine
Handles inbound replies, NLP intent classification, address parsing, and automated timer expirations.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from whatsapp.templates import render_template
from engine.llm_verifier import LLMAddressVerifier


class FlowManager:
    """Manages the full two-way WhatsApp conversation lifecycle for COD orders."""

    def __init__(self):
        self.llm_verifier = LLMAddressVerifier()

    def create_session(self, order: Dict[str, Any], action: str, lang: str = "hinglish") -> Dict[str, Any]:
        """Initializes a new WhatsApp conversation session for an order."""
        order_id = str(order.get("order_id", "UNKNOWN"))
        customer_name = str(order.get("customer_name", "Customer"))
        order_value = float(order.get("order_value", 649))
        discounted_value = max(0, order_value - 50)
        items = str(order.get("items", "Haircare Essentials"))
        address = str(order.get("address", ""))
        city = str(order.get("city", ""))
        state = str(order.get("state", ""))
        pincode = str(order.get("pincode", "")).replace(".0", "")

        payment_link = f"https://pay.keshveda.in/upi?order_id={order_id}&amount={int(discounted_value)}"

        # Initial Outbound Message
        template_key = "nudge_prepaid" if action == "Nudge to prepaid" else "confirmation"
        outbound_msg = render_template(
            template_key=template_key,
            lang=lang,
            customer_name=customer_name,
            order_id=order_id,
            order_value=int(order_value),
            discounted_value=int(discounted_value),
            items=items,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            payment_link=payment_link
        )

        session = {
            "order_id": order_id,
            "customer_name": customer_name,
            "action": action,
            "lang": lang,
            "order_value": order_value,
            "discounted_value": discounted_value,
            "original_address": f"{address}, {city}, {state} - {pincode}",
            "current_address": f"{address}, {city}, {state} - {pincode}",
            "state": "AWAITING_REPLY",
            "created_at": datetime.now().isoformat(),
            "messages": [
                {
                    "sender": "bot",
                    "text": outbound_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p"),
                    "action_type": action
                }
            ],
            "dispatch_status": "ON_HOLD",
            "payment_status": "COD_PENDING"
        }
        return session

    def process_incoming_message(self, session: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """
        Processes incoming text from the customer, updates state, and generates response.
        """
        clean_text = user_text.strip()
        lower_text = clean_text.lower()
        order_id = session["order_id"]
        customer_name = session["customer_name"]
        lang = session.get("lang", "hinglish")

        # Record user message in history
        session["messages"].append({
            "sender": "user",
            "text": clean_text,
            "timestamp": datetime.now().strftime("%I:%M %p")
        })

        # 1. Check for Positive Confirmation
        # e.g., "1", "yes", "ha", "haan", "confirm", "bhejo", "kar do", "send it", "deliver", "ok"
        confirm_patterns = [
            r'^(1|yes|ha|haan|haa|yep|confirm|confirmed|bhejo|kar do|send|ok|okay|deliver|bhej do)$',
            r'\b(confirm|bhej do|kar do|jaldi bhejo|deliver kar do)\b'
        ]
        is_confirm = any(re.search(pat, lower_text) for pat in confirm_patterns)

        # 2. Check for Cancellation Intent
        # e.g., "2", "no", "nahi", "cancel", "mat bhejo", "don't send", "wrong order"
        cancel_patterns = [
            r'^(2|no|nahi|nah|cancel|cancelled|mat bhejo|dont send|don\'t send|galat order)$',
            r'\b(cancel kar do|mat bhejo|nahi chahiye|by mistake)\b'
        ]
        is_cancel = any(re.search(pat, lower_text) for pat in cancel_patterns)

        # 3. Check for Prepaid Conversion / Payment confirmation
        # e.g., "paid", "done payment", "upi kar diya", "paid via gpay", "payment done"
        paid_patterns = [
            r'\b(paid|payment done|pay kar diya|upi kar diya|gpay kar diya|phonepe done)\b'
        ]
        is_paid = any(re.search(pat, lower_text) for pat in paid_patterns)

        # 4. Check for Address Update / Landmark Input
        # e.g., "flat 204", "house no 12", "near shiv mandir", "mera address hai: ..."
        addr_cues = ['flat', 'house', 'h.no', 'hno', 'room', 'floor', 'opp', 'near', 'mandir', 'colony', 'gali', 'chowk', 'address']
        is_addr_update = any(cue in lower_text for cue in addr_cues) and len(clean_text) > 8

        # Execute State Transitions
        if is_paid:
            session["state"] = "PREPAID_CONVERTED"
            session["dispatch_status"] = "APPROVED_FOR_DISPATCH"
            session["payment_status"] = "PREPAID_UPI"
            reply_text = render_template(
                "prepaid_converted_response",
                lang=lang,
                customer_name=customer_name,
                order_id=order_id,
                discounted_value=int(session["discounted_value"])
            )

        elif is_cancel:
            session["state"] = "CANCELLED_BY_CUSTOMER"
            session["dispatch_status"] = "CANCELLED_AVOIDED_RTO"
            session["payment_status"] = "CANCELLED"
            reply_text = render_template(
                "cancelled_response",
                lang=lang,
                customer_name=customer_name,
                order_id=order_id
            )

        elif is_confirm:
            session["state"] = "CONFIRMED_BY_CUSTOMER"
            session["dispatch_status"] = "APPROVED_FOR_DISPATCH"
            reply_text = render_template(
                "confirmed_response",
                lang=lang,
                customer_name=customer_name,
                order_id=order_id
            )

        elif is_addr_update:
            # Extract and update address
            updated_addr = clean_text
            # Remove filler words like "address is", "mera address", etc.
            updated_addr = re.sub(r'^(mera address hai|address is|new address|address)\s*[:=-]?\s*', '', updated_addr, flags=re.IGNORECASE)
            session["current_address"] = f"{updated_addr} (Verified via WhatsApp)"
            session["state"] = "CONFIRMED_WITH_UPDATED_ADDRESS"
            session["dispatch_status"] = "APPROVED_FOR_DISPATCH"
            reply_text = render_template(
                "address_updated_response",
                lang=lang,
                customer_name=customer_name,
                order_id=order_id,
                new_address=updated_addr
            )

        else:
            # Random question or ambiguous reply
            # Handle standard customer inquiries
            if any(w in lower_text for w in ['kab', 'when', 'delivery', 'din', 'days', 'time']):
                ans = "Delivery usually takes 3 to 5 business days across India! 🚚"
            elif any(w in lower_text for w in ['return', 'exchange', 'policy']):
                ans = "We offer a 7-day hassle-free return/replacement on damaged products! 🛡️"
            elif any(w in lower_text for w in ['cod', 'cash']):
                ans = f"Yes, Cash on Delivery is available for ₹{int(session['order_value'])}. 💵"
            else:
                ans = "Thank you for reaching out!"

            if lang == "hinglish":
                reply_text = f"{ans}\n\nAapke order #{order_id} ko dispatch karne ke liye, kripya *Reply 1* to Confirm karein ya *Reply 2* to Cancel karein! 🙏"
            else:
                reply_text = f"{ans}\n\nTo release order #{order_id} for shipping, please *Reply 1* to Confirm or *Reply 2* to Cancel! 🙏"

        # Record bot reply
        session["messages"].append({
            "sender": "bot",
            "text": reply_text,
            "timestamp": datetime.now().strftime("%I:%M %p")
        })

        return session

    def trigger_timer_event(self, session: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Simulates automated background cron triggers: T+12h reminder or T+24h auto-cancel."""
        order_id = session["order_id"]
        customer_name = session["customer_name"]
        lang = session.get("lang", "hinglish")

        if session["state"] not in ["AWAITING_REPLY", "REMINDER_SENT"]:
            return session  # Already terminal state

        if event_type == "12h_reminder":
            session["state"] = "REMINDER_SENT"
            msg = render_template("reminder_12h", lang=lang, customer_name=customer_name, order_id=order_id)
        elif event_type == "24h_auto_cancel":
            session["state"] = "EXPIRED_AUTO_CANCEL"
            session["dispatch_status"] = "AUTO_CANCELLED_UNRESPONSIVE"
            session["payment_status"] = "EXPIRED"
            msg = render_template("auto_cancel_24h", lang=lang, customer_name=customer_name, order_id=order_id)
        else:
            return session

        session["messages"].append({
            "sender": "bot",
            "text": msg,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "event": event_type
        })
        return session
