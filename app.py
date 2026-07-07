from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ai_parser import parse_trader_message, format_buyer_results
from ai_parser import parse_trader_message, format_buyer_results
from sheets import add_listing, search_listings
from sheets import add_listing, search_listings
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

TRADER_KEYWORDS = [
    "fresh",
    "selling",
    "available",
    "i get",
    "i have",
    "naira",
    "pieces",
    "kg",
    "stall",
]
BUYER_KEYWORDS = [
    "find",
    "looking",
    "where",
    "buy",
    "price",
    "any",
    "who get",
    "who has",
]


def is_trader_message(message):
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in TRADER_KEYWORDS)


def is_buyer_message(message):
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in BUYER_KEYWORDS)


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "").strip()
    sender_phone = request.form.get("From", "")
    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("Send your stock update or search for a product.")
        return str(resp)

    if is_trader_message(incoming_msg):
        try:
            parsed = parse_trader_message(incoming_msg)
            if parsed.get("confidence") == "low":
                msg.body(
                    "I couldn't read that clearly. Try again like this:\n"
                    "'Fresh croaker 20 pieces 4500 naira Igbudu stall 14'"
                )
            else:
                add_listing(parsed, sender_phone)
                msg.body(
                    f"Stock listed! ✅\n"
                    f"Product: {parsed.get('product')}\n"
                    f"Quantity: {parsed.get('quantity')}\n"
                    f"Price: {parsed.get('price')}\n"
                    f"Location: {parsed.get('location')}\n\n"
                    f"Buyers can find you now."
                )
        except Exception as e:
            import traceback
            print(f"ERROR in trader flow: {traceback.format_exc()}")
            msg.body("Something went wrong listing your stock. Please try again.")

    elif is_buyer_message(incoming_msg):
        try:
            results = search_listings(incoming_msg)
            reply = format_buyer_results(results, incoming_msg)
            msg.body(reply)
        except Exception as e:
            msg.body("Search failed. Please try again in a moment.")

    else:
        msg.body(
            "Welcome to MarketNow Warri 🛒\n\n"
            "*Traders:* Send your stock update\n"
            "Example: 'Fresh tomatoes 50kg 800 naira Igbudu stall 3'\n\n"
            "*Buyers:* Search for what you need\n"
            "Example: 'find croaker Igbudu'"
        )

    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
