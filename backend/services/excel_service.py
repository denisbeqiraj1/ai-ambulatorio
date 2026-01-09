import pandas as pd
import os
import json
import gspread
from datetime import datetime

DATA_FILE = "/data/results.xlsx"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1jItPMbpkbVBdRwdZrNj8gsxd_vk5DHD9is7houS0f54/edit?gid=0#gid=0"
CREDENTIALS_FILE = "credentials.json" # Expected in /app/credentials.json or /backend/credentials.json

def append_to_google_sheet(site_name: str, phone: str):
    """
    Appends the result to the predefined Google Sheet.
    Requries 'credentials.json' to be present.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Skipping Google Sheet export: {CREDENTIALS_FILE} not found.")
        return

    # User Helper: Check if the JSON is likely correct
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
        if creds_data.get('type') != 'service_account':
            print(f"ERROR: {CREDENTIALS_FILE} is not a Service Account key. Type found: {creds_data.get('type')}")
            print("Please create a SERVICE ACCOUNT in Google Cloud Console => IAM & Admin => Service Accounts, keys => Create JSON.")
            return
    except Exception as e:
        print(f"Error reading {CREDENTIALS_FILE}: {e}")
        return

    try:
        # Modern way using gspread (wraps google-auth)
        # It looks for the file path in params or env var, here we pass it explicitly
        client = gspread.service_account(filename=CREDENTIALS_FILE)
        
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        # Columns: [Site Name, Phone Number]
        row = [site_name, phone]
        sheet.append_row(row)
        print(f"Successfully saved to Google Sheet: {row}")
    except Exception as e:
        print(f"Error saving to Google Sheet: {e}")

def append_result(search_query: str, phone_number: str, source: str):
    """
    Appends the search result to the Excel file AND Google Sheets.
    Creates the file if it doesn't exist.
    """
    print(f"Saving result: {search_query} -> {phone_number} ({source})")
    
    # 1. Excel Save (Backup)
    new_data = {
        "Search Query": [search_query],
        "Phone Number": [phone_number],
        "Source": [source],
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    }
    df_new = pd.DataFrame(new_data)

    if os.path.exists(DATA_FILE):
        try:
            df_existing = pd.read_excel(DATA_FILE)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        except Exception as e:
            print(f"Error reading existing Excel: {e}. Creating new.")
            df_combined = df_new
    else:
        df_combined = df_new

    try:
        df_combined.to_excel(DATA_FILE, index=False)
        print("Excel file updated successfully.")
    except Exception as e:
        print(f"Error saving Excel file: {e}")

    # 2. Google Sheet Save
    append_to_google_sheet(search_query, phone_number)
