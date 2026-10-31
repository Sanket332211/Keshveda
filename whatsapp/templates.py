"""
WhatsApp Message Templates
Bilingual support: Professional Hinglish (industry gold-standard for Indian D2C) & Clean English.
"""

from typing import Dict, Any

TEMPLATES = {
    "confirmation": {
        "hinglish": (
            "Hey {customer_name}! 👋 Thank you for ordering from Keshveda!\n\n"
            "📦 *Order #{order_id}* ({items})\n"
            "💰 *Total COD Amount:* ₹{order_value}\n"
            "📍 *Delivery Address:* {address}, {city}, {state} - {pincode}\n\n"
            "Rider ko aapka ghar dhoondhne me problem na ho, please confirm karein:\n"
            "👉 *Reply 1* to CONFIRM & SHIP\n"
            "👉 *Reply 2* to CANCEL\n"
            "👉 Ya fir apna complete *Flat/House No. aur Landmark* yahan reply karein!\n\n"
            "_(24 ghante me confirm na hone par order auto-hold ho jayega)_"
        ),
        "english": (
            "Hi {customer_name}! 👋 Thank you for ordering from Keshveda!\n\n"
            "📦 *Order #{order_id}* ({items})\n"
            "💰 *COD Total:* ₹{order_value}\n"
            "📍 *Address:* {address}, {city}, {state} - {pincode}\n\n"
            "To ensure seamless doorstep delivery:\n"
            "👉 *Reply 1* to CONFIRM this order\n"
            "👉 *Reply 2* to CANCEL\n"
            "👉 Or reply with your updated House/Flat No. or Landmark!\n\n"
            "_(Orders unconfirmed after 24h are held automatically)_"
        )
    },
    "nudge_prepaid": {
        "hinglish": (
            "Hey {customer_name}! 🎉 Special prepaid offer for your order #{order_id}!\n\n"
            "⚡ *Pay Online & Get FLAT ₹50 OFF!*\n"
            "Original COD: ~₹{order_value}~\n"
            "🔥 *You Pay Only:* *₹{discounted_value}*\n\n"
            "🔗 Click here to pay via UPI (GPay/PhonePe/Paytm):\n"
            "👉 {payment_link}\n\n"
            "✨ *Benefits:* Save ₹50 + 100% Contactless Delivery + Priority Packing! 🚀\n\n"
            "_(Agar COD hi chahiye, toh 'COD' reply karein)_"
        ),
        "english": (
            "Hi {customer_name}! 🎉 Exclusive prepaid offer for order #{order_id}!\n\n"
            "⚡ *Pay online right now & get FLAT ₹50 OFF!*\n"
            "Original COD Amount: ~₹{order_value}~\n"
            "🔥 *Discounted Total:* *₹{discounted_value}*\n\n"
            "🔗 Fast 1-Click UPI Payment Link:\n"
            "👉 {payment_link}\n\n"
            "✨ *Benefits:* Save ₹50 + Zero Cash Hassle + Priority Dispatch! 🚀\n\n"
            "_(If you still prefer COD, simply reply 'COD')_"
        )
    },
    "reminder_12h": {
        "hinglish": (
            "Hi {customer_name}! ⏰ Quick reminder from Keshveda.\n\n"
            "Aapka order #{order_id} pack ho chuka hai par dispatch hold par hai. "
            "Please reply *1 to CONFIRM* taaki hum ise aaj hi ship kar sakein! 🚚"
        ),
        "english": (
            "Hi {customer_name}! ⏰ Quick reminder from Keshveda.\n\n"
            "Your order #{order_id} is packed and waiting for your confirmation. "
            "Please reply *1 to CONFIRM* so we can dispatch it today! 🚚"
        )
    },
    "auto_cancel_24h": {
        "hinglish": (
            "Order Update: Hi {customer_name}, 24 ghante me confirmation na milne par "
            "order #{order_id} ko hold/cancel kar diya gaya hai. "
            "Agar aap ise dubara activate karna chahte hain, toh bas yahan *REOPEN* reply karein! 🙏"
        ),
        "english": (
            "Order Update: Hi {customer_name}, as we did not receive confirmation within 24 hours, "
            "order #{order_id} has been placed on hold. "
            "If you still want your items, reply *REOPEN* anytime to dispatch! 🙏"
        )
    },
    "confirmed_response": {
        "hinglish": (
            "Shukriya {customer_name}! ✅ Aapka order #{order_id} confirm ho gaya hai.\n"
            "Hamari dispatch team ise pack kar rahi hai. Aapse tracking link jald hi share karenge! 📦✨"
        ),
        "english": (
            "Thank you {customer_name}! ✅ Your order #{order_id} is confirmed.\n"
            "Our dispatch team is packing your parcel. We will share live tracking shortly! 📦✨"
        )
    },
    "cancelled_response": {
        "hinglish": (
            "Ji bilkul, order #{order_id} cancel kar diya gaya hai. Koi amount nahi dena hoga. "
            "Hum aasha karte hain ki jald hi aap fir se Keshveda visit karenge! 🙏"
        ),
        "english": (
            "Noted! Order #{order_id} has been successfully cancelled. Zero amount is due. "
            "We look forward to serving you again in the future! 🙏"
        )
    },
    "address_updated_response": {
        "hinglish": (
            "Great! Humne aapka delivery address update kar diya hai:\n"
            "📍 *{new_address}*\n\n"
            "Aapka order #{order_id} ab dispatch ke liye approved hai! 🚚💨"
        ),
        "english": (
            "Great! We have updated your doorstep address to:\n"
            "📍 *{new_address}*\n\n"
            "Your order #{order_id} is now approved and ready for dispatch! 🚚💨"
        )
    },
    "prepaid_converted_response": {
        "hinglish": (
            "Payment Received! 🎉 ₹{discounted_value} successfully paid via UPI.\n"
            "Aapne ₹50 bacha liye hain! Aapka order #{order_id} priority dispatch queue me lag gaya hai. 🚀"
        ),
        "english": (
            "Payment Confirmed! 🎉 ₹{discounted_value} received via UPI.\n"
            "You saved ₹50! Your order #{order_id} has been moved to priority dispatch. 🚀"
        )
    }
}


def render_template(template_key: str, lang: str = "hinglish", **kwargs) -> str:
    """Renders a selected template with variable substitution."""
    tpl_dict = TEMPLATES.get(template_key, {})
    template_str = tpl_dict.get(lang, tpl_dict.get("english", ""))
    return template_str.format(**kwargs)
