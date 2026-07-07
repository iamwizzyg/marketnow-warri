from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ai_parser import parse_trader_message, format_buyer_results
from sheets import add_listing, search_listings
from dotenv import load_dotenv
import os
import traceback
import re

load_dotenv()

app = Flask(__name__)


def classify_message(message):
    message_lower = message.lower()

    trader_score = 0
    buyer_score = 0

    if any(w in message_lower for w in ["naira", "₦", "stall", "selling", "i get", "i have"]):
        trader_score += 3
    if any(w in message_lower for w in ["fresh", "available", "pieces", "kg", "bags", "units"]):
        trader_score += 2
    if any(char.isdigit() for char in message_lower):
        trader_score += 1

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
    message_lower = message.lower()
    if any(w in message_lower for w in ["under", "below", "less than", "cheaper than", "max"]):
        numbers = re.findall(r'[\d,]+', message)
        if numbers:
            return int(numbers[-1].replace(',', ''))
    return None


def welcome_message():
    return (
        "👋 Welcome to *MarketNow Warri* 🛒\n"
        "Built by Uche Wisdom Godwin | 3MTT Fellow, Delta State\n\n"
        "I connect market traders and buyers in Warri in real time.\n"
        "No app download needed — just WhatsApp.\n\n"
        "*📦 Are you a TRADER?*\n"
        "Send your stock like this:\n"
        "'Fresh croaker 20 pieces 4500 naira Igbudu stall 14'\n\n"
        "*🛍️ Are you a BUYER?*\n"
        "Search like this:\n"
        "'find croaker Igbudu'\n"
        "'where can I buy tomatoes under ₦3000'\n\n"
        "Type HELP anytime to see this again."
    )


@app.route("/", methods=["GET"])
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarketNow Warri</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
        }
        .hero {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 60px 20px;
            text-align: center;
            border-bottom: 1px solid #1e3a5f;
        }
        .badge {
            display: inline-block;
            background: rgba(0, 200, 100, 0.15);
            border: 1px solid rgba(0, 200, 100, 0.4);
            color: #00c864;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }
        .hero h1 {
            font-size: clamp(2rem, 6vw, 3.5rem);
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #a8d8ea);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
            line-height: 1.2;
        }
        .hero p {
            font-size: clamp(1rem, 2.5vw, 1.2rem);
            color: #8899aa;
            max-width: 560px;
            margin: 0 auto 40px;
            line-height: 1.6;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin-top: 40px;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: 800;
            color: #00c864;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #667788;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }
        .section {
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 20px;
        }
        .section-title {
            text-align: center;
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 40px;
        }
        .section-title span { color: #00c864; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 60px;
        }
        .card {
            background: #111827;
            border: 1px solid #1e2d40;
            border-radius: 16px;
            padding: 28px;
            transition: border-color 0.3s, transform 0.3s;
        }
        .card:hover {
            border-color: #00c864;
            transform: translateY(-4px);
        }
        .card-icon { font-size: 2rem; margin-bottom: 16px; }
        .card h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }
        .card p { font-size: 0.9rem; color: #667788; line-height: 1.6; }
        .demo-section {
            background: #111827;
            border: 1px solid #1e2d40;
            border-radius: 20px;
            padding: 40px 20px;
            text-align: center;
            max-width: 900px;
            margin: 0 auto 60px;
        }
        .demo-section h2 { font-size: 1.5rem; font-weight: 700; margin-bottom: 12px; }
        .demo-section > p { color: #667788; margin-bottom: 32px; font-size: 0.95rem; }
        .demo-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 32px;
            text-align: left;
        }
        @media (max-width: 600px) { .demo-grid { grid-template-columns: 1fr; } }
        .demo-box {
            background: #0a0a0a;
            border: 1px solid #1e2d40;
            border-radius: 12px;
            padding: 20px;
        }
        .demo-box-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #00c864;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .demo-message {
            background: #1a2740;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.85rem;
            color: #a8d8ea;
            margin-bottom: 8px;
            font-family: monospace;
        }
        .demo-reply {
            background: #0d1f0d;
            border: 1px solid #1a3a1a;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.85rem;
            color: #00c864;
            font-family: monospace;
            white-space: pre-line;
        }
        .qr-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            margin-top: 32px;
        }
        .qr-box {
            background: #ffffff;
            padding: 16px;
            border-radius: 16px;
            display: inline-block;
        }
        .qr-box img { width: 160px; height: 160px; display: block; }
        .qr-label { font-size: 0.85rem; color: #667788; text-align: center; }
        .join-code {
            background: #0d1f0d;
            border: 1px solid #1a3a1a;
            border-radius: 8px;
            padding: 10px 20px;
            font-family: monospace;
            color: #00c864;
            font-size: 0.9rem;
        }
        .footer {
            border-top: 1px solid #1e2d40;
            padding: 30px 20px;
            text-align: center;
            color: #445566;
            font-size: 0.85rem;
        }
        .footer strong { color: #667788; }
        .live-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00c864;
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>

<div class="hero">
    <div class="badge">🟢 Live — Delta State, Nigeria</div>
    <h1>MarketNow Warri</h1>
    <p>Real-time market availability for Warri traders and buyers — powered by WhatsApp. No app download. No registration. Just send a message.</p>
    <div class="stats">
        <div class="stat">
            <div class="stat-number">3</div>
            <div class="stat-label">Markets Covered</div>
        </div>
        <div class="stat">
            <div class="stat-number">0s</div>
            <div class="stat-label">App Download Time</div>
        </div>
        <div class="stat">
            <div class="stat-number">24/7</div>
            <div class="stat-label">Availability</div>
        </div>
    </div>
</div>

<div class="section">
    <h2 class="section-title">Why <span>MarketNow</span>?</h2>
    <div class="cards">
        <div class="card">
            <div class="card-icon">🚌</div>
            <h3>Buyers Waste Trips</h3>
            <p>Buyers travel to Igbudu, Enerhen, and PTI Road only to find stock sold out. Transport money wasted. Time lost.</p>
        </div>
        <div class="card">
            <div class="card-icon">📉</div>
            <h3>Traders Lose Sales</h3>
            <p>Traders with fresh stock have no way to reach buyers before they make the trip. Sales die silently every day.</p>
        </div>
        <div class="card">
            <div class="card-icon">💬</div>
            <h3>WhatsApp Is Already There</h3>
            <p>Every trader and buyer in Warri already uses WhatsApp daily. MarketNow works inside the app they already know.</p>
        </div>
    </div>
</div>

<div class="demo-section">
    <h2>See It In Action</h2>
    <p>Real conversations. Real market data. Real time.</p>
    <div class="demo-grid">
        <div class="demo-box">
            <div class="demo-box-title">📦 Trader Lists Stock</div>
            <div class="demo-message">Fresh croaker 20 pieces 4500 naira Igbudu stall 14</div>
            <div class="demo-reply">Stock listed! ✅
Product: croaker
Quantity: 20 pieces
Price: ₦4500
Location: Igbudu
Buyers can find you now.</div>
        </div>
        <div class="demo-box">
            <div class="demo-box-title">🛍️ Buyer Searches Stock</div>
            <div class="demo-message">where can I buy croaker under ₦5000</div>
            <div class="demo-reply">Here's what I found 👇

Product: croaker
Price: ₦4500
Quantity: 20 pieces
Location: Igbudu
Stall: 14</div>
        </div>
    </div>

    <h3 style="margin-bottom: 16px; font-size: 1.1rem;">Try It Live on WhatsApp</h3>
    <div class="qr-section">
        <div class="qr-box">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https://wa.me/14155238886?text=join%20atomic-statement" alt="Scan to test on WhatsApp" />
        </div>
        <div class="qr-label">Scan with your phone camera to open WhatsApp</div>
        <div class="join-code">First send: join atomic-statement</div>
        <div class="qr-label">Then send any trader or buyer message to test</div>
    </div>
</div>

<div class="footer">
    <p><span class="live-dot"></span><strong>MarketNow Warri</strong> — Built by Uche Wisdom Godwin</p>
    <p style="margin-top: 6px;">3MTT Fellow, Delta State &nbsp;|&nbsp; Airtel NextGen Cohort Knowledge Showcase 2.0</p>
    <p style="margin-top: 6px;">Stack: Python &middot; Flask &middot; Twilio &middot; Google Sheets &middot; Render</p>
</div>

</body>
</html>
"""


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

    if incoming_msg.lower() in ["help", "hi", "hello", "start", "menu", "hey"]:
        msg.body(welcome_message())
        return str(resp)

    intent = classify_message(incoming_msg)

    if intent == "trader":
        try:
            print("DEBUG: Processing trader message", flush=True)
            parsed = parse_trader_message(incoming_msg)
            print(f"DEBUG: Parsed = {parsed}", flush=True)
            add_listing(parsed, sender_phone)
            print("DEBUG: Listing added successfully", flush=True)
            msg.body(
                f"Stock listed! ✅\n"
                f"Product: {parsed.get('product')}\n"
                f"Quantity: {parsed.get('quantity')}\n"
                f"Price: {parsed.get('price')}\n"
                f"Location: {parsed.get('location')}\n"
                f"Stall: {parsed.get('stall')}\n\n"
                f"Buyers can find you now.\n"
                f"Send HELP to see all commands."
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
        msg.body(welcome_message())

    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
