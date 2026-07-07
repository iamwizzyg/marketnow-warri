import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheet():
    import json
    import os
    print("DEBUG: Attempting to load GOOGLE_CREDENTIALS")
    creds_raw = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_raw:
        print("DEBUG: GOOGLE_CREDENTIALS is None or empty")
        raise ValueError("GOOGLE_CREDENTIALS not set")
    print(f"DEBUG: GOOGLE_CREDENTIALS length = {len(creds_raw)}")
    creds_json = json.loads(creds_raw)
    print(f"DEBUG: JSON parsed, client_email = {creds_json.get('client_email')}")
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
    return sheet.sheet1


def add_listing(parsed_data, phone):
    try:
        sheet = get_sheet()
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            parsed_data.get("product", "not specified"),
            parsed_data.get("quantity", "not specified"),
            parsed_data.get("price", "not specified"),
            parsed_data.get("location", "not specified"),
            parsed_data.get("stall", "not specified"),
            phone
        ]
        print(f"WRITING ROW: {row}", flush=True)
        sheet.append_row(row)
        print("ROW WRITTEN SUCCESSFULLY", flush=True)
        return True
    except Exception as e:
        import traceback
        print(f"SHEETS ERROR: {traceback.format_exc()}", flush=True)
        raise

def search_listings(query, price_limit=None):
    sheet = get_sheet()
    all_rows = sheet.get_all_records()
    skip_words = ["find", "looking", "where", "buy", "price", "any", "who",
                  "get", "has", "for", "can", "i", "under", "below", "cheap",
                  "less", "than", "how", "much", "what", "igbudu", "enerhen", "warri"]
    query_words = [w.lower() for w in query.split() if w.lower() not in skip_words]

    matches = []
    for row in all_rows:
        product = str(row.get("Product", "")).lower()
        location = str(row.get("Location", "")).lower()
        for word in query_words:
            if word in product or word in location:
                if price_limit:
                    try:
                        import re
                        price_str = str(row.get("Price", "0"))
                        price_num = int(re.sub(r'[^\d]', '', price_str))
                        if price_num <= price_limit:
                            matches.append(row)
                    except:
                        matches.append(row)
                else:
                    matches.append(row)
                break
    return matches[:5]


def clear_old_listings():
    sheet = get_sheet()
    all_rows = sheet.get_all_records()
    now = datetime.now()
    rows_to_keep = []
    for row in all_rows:
        try:
            ts = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M")
            if (now - ts).total_seconds() < 86400:
                rows_to_keep.append(row)
        except:
            pass
    return rows_to_keep
