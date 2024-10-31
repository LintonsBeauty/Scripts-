import requests
import json
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheets and Trello credentials
GOOGLE_SHEET_ID = '14XaB6adn7MWdWS4BacZVPOgRwbVpjPJoP0b-rFC4BFk'
GOOGLE_SHEET_NAME = 'Form Responses 1'
GOOGLE_CREDENTIALS_FILE = 'crested-trainer-292909-509d7f962395.json'

TRELLO_KEY = 'de191ae0dcf871ec94a2c3a9e301f9ff'
TRELLO_TOKEN = 'ATTAa60e29643e75d864c757c0e614df0174ad436b9dbbbf7f99a36f9c51cf3799be0DD6667E'
BOARD_ID = '66c097ffa07e57790a36a234'
LIST_ID = '63c00d1b02ad370027927314'  # List title "incoming"

# Set up Google Sheets API client
def get_google_sheet_data():
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    # Get all data from the sheet starting from row 2 (skipping headers)
    result = sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=f"{GOOGLE_SHEET_NAME}!A2:I").execute()
    return result.get('values', [])

# Function to create a Trello card
def create_trello_card(title, description):
    url = f"https://api.trello.com/1/cards"
    query = {
        'key': TRELLO_KEY,
        'token': TRELLO_TOKEN,
        'idList': LIST_ID,
        'name': title,
        'desc': description
    }
    
    response = requests.post(url, params=query)
    if response.status_code == 200:
        print(f"Card '{title}' created successfully.")
        return response.json()  # Return card data for later reference
    else:
        print(f"Failed to create card '{title}'. Error: {response.text}")
        return None

# Function to get last scanned row from a file
def get_last_scanned_row():
    try:
        with open('last_row.txt', 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 1  # Default to 1 if file not found or invalid value

# Function to store the last scanned row in a file
def store_last_scanned_row(row):
    with open('last_row.txt', 'w') as f:
        f.write(str(row))

# Main function to sync Google Sheets data to Trello
def sync_google_sheet_to_trello():
    last_scanned_row = get_last_scanned_row()
    processed_rows = set()  # Track processed rows
    trello_cards = {}  # Map to track Trello cards created

    while True:
        rows = get_google_sheet_data()
        current_row_count = len(rows)

        # Print debug information
        print(f"Last scanned row: {last_scanned_row}, Current row count: {current_row_count}")

        # Reset last scanned row if it exceeds current row count
        if last_scanned_row > current_row_count:
            print(f"Last scanned row {last_scanned_row} exceeds current row count {current_row_count}. Resetting last scanned row to {current_row_count}.")
            last_scanned_row = current_row_count
            store_last_scanned_row(last_scanned_row)

        # Check for new rows to process
        for new_row_index in range(last_scanned_row - 1, current_row_count):
            if new_row_index not in processed_rows:  # Only process rows that haven't been processed yet
                row = rows[new_row_index]
                # Ensure row has at least 9 columns
                if len(row) < 9:
                    row.extend([''] * (9 - len(row)))  # Add empty strings to fill missing columns

                # Format title and description
                title = f"Receipt Reprint ({row[1]})"  # Store Name in parentheses for card title (Column B)
                description = (
                    f"Timestamp: {row[0]}\n"  # Column A
                    f"Receipt Number: {row[2]}\n"  # Column C
                    f"Sales Rep: {row[3]}\n"  # Column D
                    f"Receipt Date: {row[4]}\n"  # Column E
                    f"Mode of Payment: {row[5]}\n"  # Column F
                    f"Total Amount: {row[6]}\n"  # Column G
                    f"Purpose: {row[7]}\n"  # Column H
                    f"Email Address: {row[8]}"  # Column I
                )

                # Create Trello card only for the new row
                card_data = create_trello_card(title, description)

                if card_data:
                    # Save the Trello card ID to track it
                    trello_cards[new_row_index] = card_data['id']

                # Mark the row as processed
                processed_rows.add(new_row_index)

                # Update the last scanned row number after processing new row
                last_scanned_row = new_row_index + 1  # Move to the next row
                store_last_scanned_row(last_scanned_row)  # Store updated last scanned row
                print(f"Processed row {new_row_index + 1}. Updated last scanned row to {last_scanned_row}.")

        # Check for deleted rows
        deleted_rows = [index for index in processed_rows if index >= current_row_count]
        for index in deleted_rows:
            # Handle deleted rows
            print(f"Row {index + 2} has been deleted from the sheet.")  # +2 to account for header and 0-based index
            # You can add additional logic here to handle Trello cards (e.g., removing or archiving)
            del processed_rows[index]
            del trello_cards[index]  # Remove from tracked cards

        if current_row_count == last_scanned_row - 1:
            print("No new rows found. Waiting for the next check.")

        # Wait for 5 seconds before checking again
        time.sleep(5)

# Execute the sync function
sync_google_sheet_to_trello()

