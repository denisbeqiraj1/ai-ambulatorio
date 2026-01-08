import pandas as pd
import os
from datetime import datetime

DATA_FILE = "/data/results.xlsx"

def append_result(search_query: str, phone_number: str, source: str):
    """
    Appends the search result to the Excel file.
    Creates the file if it doesn't exist.
    """
    print(f"Saving result: {search_query} -> {phone_number} ({source})")
    
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
