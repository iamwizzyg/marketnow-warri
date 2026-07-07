from google import genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def parse_trader_message(message):
    prompt = f"""
You are a market assistant in Warri, Nigeria.
A trader just sent this WhatsApp message: "{message}"
The message may be in English, Pidgin English, or broken English.

Extract the following and return ONLY valid JSON, nothing else:
{{
  "product": "name of product",
  "quantity": "number and unit",
  "price": "price in naira",
  "location": "market or area name",
  "stall": "stall number or description if mentioned",
  "confidence": "high/medium/low based on how clear the message was"
}}

If any field is missing from the message, use "not specified".
Return ONLY the JSON object. No explanation. No markdown.
"""
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    raw = response.text.strip()
    return json.loads(raw)


def format_buyer_results(results, query):
    if not results:
        return "No listings found for that item right now. Try again later or check another market."

    prompt = f"""
A buyer in Warri is looking for: "{query}"
Here are the current listings from traders:
{json.dumps(results, indent=2)}

Write a short, friendly WhatsApp reply (max 5 lines) listing what's available.
Include product, price, quantity, location and stall number.
Write in simple English. Be concise. No bullet symbols that don't render on WhatsApp.
Start with: "Here's what I found 👇"
"""
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip()
