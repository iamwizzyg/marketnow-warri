import json

def parse_trader_message(message):
    words = message.lower().split()
    original_words = message.split()
    
    # Find product (word after "fresh" or first noun)
    product = "not specified"
    for i, w in enumerate(words):
        if w in ["fresh", "selling", "available"] and i+1 < len(original_words):
            product = original_words[i+1]
            break
    if product == "not specified" and original_words:
        product = original_words[0]

    # Find quantity
    quantity = "not specified"
    for i, w in enumerate(words):
        if w.isdigit():
            unit = words[i+1] if i+1 < len(words) else "pieces"
            quantity = f"{w} {unit}"
            break

    # Find price (number before "naira")
    price = "not specified"
    for i, w in enumerate(words):
        if w == "naira" and i > 0:
            price = f"₦{words[i-1]}"
            break

    # Find location
    markets = ["igbudu", "enerhen", "ptd", "ekurede", "warri", "effurun", "ugborikoko"]
    location = "not specified"
    for w in words:
        if w in markets:
            location = w.title()
            break

    # Find stall
    stall = "not specified"
    for i, w in enumerate(words):
        if w == "stall" and i+1 < len(words):
            stall = words[i+1]
            break

    return {
        "product": product,
        "quantity": quantity,
        "price": price,
        "location": location,
        "stall": stall,
        "confidence": "high"
    }


def format_buyer_results(results, query):
    if not results:
        return "No listings found for that item right now. Try again later or check another market."
    
    reply = "Here's what I found 👇\n\n"
    for r in results[:3]:
        reply += (
            f"Product: {r.get('Product', 'N/A')}\n"
            f"Price: {r.get('Price', 'N/A')}\n"
            f"Quantity: {r.get('Quantity', 'N/A')}\n"
            f"Location: {r.get('Location', 'N/A')}\n"
            f"Stall: {r.get('Stall', 'N/A')}\n\n"
        )
    return reply.strip()
