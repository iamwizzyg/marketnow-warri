from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ai_parser import parse_trader_message, format_buyer_results
from sheets import add_listing, search_listings
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

app = Flask(__name__)

def classify_message(message):
    message_lower = message.lower()
    
    trader_score = 0
    buyer_score = 0
    
    # Strong trader signals
    if any(w in message_lower for w in ["naira", "₦", "stall", "selling", "i get", "i have"]):
        trader_score += 3
    if any(w in message_lower for w in ["fresh", "available", "pieces", "kg", "bags", "units"]):
        trader_score += 2
    if any(char.isdigit() for char in message_lower):
        trader_score += 1

    # Strong buyer signals
    if any(w in message_lower for w in ["find", "looking for", "where can", "who has", "who get", "any"]):
        buyer_score += 3
    if any(w in message_lower for w in ["buy", "price", "how much", "cost", "under", "cheap"]):
        buyer_score += 2
    if message_lower.startswith(("find", "where", "who", "any", "looking", "how much", "what")):
        buyer_score += 2

    print(f"CLASSIFY: trader={trader_score} buyer={buyer_score} msg='{message}'", flush=True)

    if buyer_score > trader_score:
        return "buyer"
    elif trader_score > buyer_score:
        return "trader"
    else:
        return "unknown"


def extract_price_limit(message):
    """Extract price ceiling from messages like 'under 5000' or 'below ₦5000'"""
    import re
    message_lower = message.lower()
    
    if any(w in message_lower for w in ["under", "below", "less than", "cheaper than", "max"]):
        numbers = re.findall(r'[\d,]+', message)
        if numbers:
            return int(numbers[-1].replace(',', ''))
    return None


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "").strip()
    sender_phone = request.form.get("From", "")
    resp = MessagingResponse()
    msg = resp.message()

    print(f"INCOMING: '{incoming_msg}' from {sender_phone}", flush=True)

    if not incoming_msg:
        msg.body("Send your stock update or search for a product.")
        return str(resp)

    intent = classify_message(incoming_msg)

    if intent == "trader":
        try:
            print("DEBUG: Processing trader message", flush=True)
            parsed = parse_trader_message(incoming_msg)
            print(f"DEBUG: Parsed = {parsed}", flush=True)
            add_listing(parsed, sender_phone)
            print("DEBUG: Listing added", flush=True)
            msg.body(
                f"Stock listed! ✅\n"
                f"Product: {parsed.get('product')}\n"
                f"Quantity: {parsed.get('quantity')}\n"
                f"Price: {parsed.get('price')}\n"
                f"Location: {parsed.get('location')}\n"
                f"Stall: {parsed.get('stall')}\n\n"
                f"Buyers can find you now."
            )
        except Exception as e:
            print(f"ERROR in trader flow: {traceback.format_exc()}", flush=True)
            msg.body("Something went wrong listing your stock. Please try again.")

    elif intent == "buyer":
        try:
            print("DEBUG: Processing buyer message", flush=True)
            price_limit = extract_price_limit(incoming_msg)
            results = search_listings(incoming_msg, price_limit)
            print(f"DEBUG: Found {len(results)} results", flush=True)
            reply = format_buyer_results(results, incoming_msg)
            msg.body(reply)
        except Exception as e:
            print(f"ERROR in buyer flow: {traceback.format_exc()}", flush=True)
            msg.body("Search failed. Please try again in a moment.")

    else:
        msg.body(
            "Welcome to MarketNow Warri 🛒\n\n"
            "*Traders:* Send your stock update\n"
            "Example: 'Fresh croaker 20 pieces 4500 naira Igbudu stall 14'\n\n"
            "*Buyers:* Search for what you need\n"
            "Example: 'find croaker Igbudu'\n"
            "Example: 'where can I buy tomatoes under ₦3000'"
        )

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
