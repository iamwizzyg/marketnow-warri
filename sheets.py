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
    creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
    return sheet.sheet1


def add_listing(parsed_data, phone):
    sheet = get_sheet()
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        parsed_data.get("product", "not specified"),
        parsed_data.get("quantity", "not specified"),
        parsed_data.get("price", "not specified"),
        parsed_data.get("location", "not specified"),
        parsed_data.get("stall", "not specified"),
        phone,
    ]
    sheet.append_row(row)
    return True


def search_listings(query):
    sheet = get_sheet()
    all_rows = sheet.get_all_records()
    query_lower = query.lower()
    matches = [
        row
        for row in all_rows
        if query_lower in str(row.get("Product", "")).lower()
        or query_lower in str(row.get("Location", "")).lower()
    ]
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
