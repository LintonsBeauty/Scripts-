import os
import requests
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from time import sleep
from datetime import datetime

# Set up Trello API credentials
TRELLO_KEY = 'de191ae0dcf871ec94a2c3a9e301f9ff'
TRELLO_TOKEN = 'ATTAa60e29643e75d864c757c0e614df0174ad436b9dbbbf7f99a36f9c51cf3799be0DD6667E'
BOARD_ID = '5fd8d581dcdab3556cae92e3'

# Set up Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '11BUXE7QUgzIBGdHZQcEeF9U6HT3hIDSfqSQj2keS1GA'

# Path to your credentials file
CREDENTIALS_FILE = 'crested-trainer-292909-509d7f962395.json'

def authenticate_google_sheets():
    """Authenticate and return Google Sheets API service."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def get_trello_lists():
    """Fetch all lists from the Trello board."""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
    query = {
        'key': TRELLO_KEY,
        'token': TRELLO_TOKEN
    }
    response = requests.get(url, params=query)
    return response.json()

def get_trello_cards():
    """Fetch all cards from Trello board."""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    query = {
        'key': TRELLO_KEY,
        'token': TRELLO_TOKEN
    }
    response = requests.get(url, params=query)
    return response.json()

def organize_cards_by_list(lists, cards):
    """Organize cards under their respective lists."""
    data = {}
    for lst in lists:
        data[lst['name']] = []
    for card in cards:
        list_name = next(lst['name'] for lst in lists if lst['id'] == card['idList'])
        data[list_name].append(card)
    return data

def track_changes(old_cards, new_cards):
    """Track changes between old and new cards."""
    changes = []
    old_card_ids = {card['id']: card for card in old_cards}
    new_card_ids = {card['id']: card for card in new_cards}
    
    # Check for deletions and edits
    for card_id, old_card in old_card_ids.items():
        if card_id not in new_card_ids:
            changes.append({
                'action': 'DELETED',
                'card_name': old_card['name'],
                'old_list': old_card['idList'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            new_card = new_card_ids[card_id]
            if old_card != new_card:
                changes.append({
                    'action': 'EDITED',
                    'card_name': new_card['name'],
                    'old_content': old_card['desc'],
                    'new_content': new_card['desc'],
                    'old_list': old_card['idList'],
                    'new_list': new_card['idList'],
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    # Check for additions and moves
    for card_id, new_card in new_card_ids.items():
        if card_id not in old_card_ids:
            changes.append({
                'action': 'ADDED',
                'card_name': new_card['name'],
                'list': new_card['idList'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            old_card = old_card_ids[card_id]
            if old_card['idList'] != new_card['idList']:
                changes.append({
                    'action': 'MOVED',
                    'card_name': new_card['name'],
                    'old_list': old_card['idList'],
                    'new_list': new_card['idList'],
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    return changes


def update_google_sheet(service, organized_data):
    """Update Google Sheets with Trello list names and cards."""
    headers = list(organized_data.keys())
    values = [headers]
    
    max_cards = max(len(cards) for cards in organized_data.values())
    for i in range(max_cards):
        row = []
        for list_name in headers:
            card = organized_data[list_name][i] if i < len(organized_data[list_name]) else ''
            row.append(card['name'] if card else '')
        values.append(row)
    
    body = {'values': values}
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range='A1',
            valueInputOption='RAW', body=body).execute()
        print("Google Sheet updated with card data.")
    except HttpError as error:
        print(f"An error occurred: {error}")

def update_change_log(service, changes):
    """Update Google Sheets with changes log."""
    change_log = [["Action", "Card Name", "Old Content", "New Content", "Old List", "New List", "Timestamp"]]
    
    for change in changes:
        log_entry = [
            change.get('action', ''),
            change.get('card_name', ''),
            change.get('old_content', ''),
            change.get('new_content', ''),
            change.get('old_list', ''),
            change.get('new_list', ''),
            change.get('timestamp', '')
        ]
        change_log.append(log_entry)

    body = {'values': change_log}
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range='Sheet2!A1',
            valueInputOption='RAW', body=body).execute()
        print("Google Sheet updated with changes log.")
    except HttpError as error:
        print(f"An error occurred: {error}")

def format_first_row(service):
    """Format the first row of both sheets."""
    requests = [
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,  # Sheet1 ID
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 7
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 12,
                            'foregroundColor': {
                                'red': 0,
                                'green': 0,
                                'blue': 0
                            }
                        },
                        'backgroundColor': {
                            'red': 0.9,
                            'green': 0.9,
                            'blue': 0.9
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat, backgroundColor)'
            }
        },
        {
            'repeatCell': {
                'range': {
                    'sheetId': 1,  # Sheet2 ID
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 7
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 12,
                            'foregroundColor': {
                                'red': 0,
                                'green': 0,
                                'blue': 0
                            }
                        },
                        'backgroundColor': {
                            'red': 0.9,
                            'green': 0.9,
                            'blue': 0.9
                   }
                    }
                },
                'fields': 'userEnteredFormat(textFormat, backgroundColor)'
            }
        }
    ]

    body = {
        'requests': requests
    }

    try:
        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        print("Formatted the first row of both sheets.")
    except HttpError as error:
        print(f"An error occurred while formatting: {error}")

def sync_data():
    """Main function to sync data between Trello and Google Sheets."""
    service = authenticate_google_sheets()

    old_cards = []
    
    while True:
        trello_lists = get_trello_lists()
        trello_cards = get_trello_cards()

        organized_data = organize_cards_by_list(trello_lists, trello_cards)
        update_google_sheet(service, organized_data)

        changes = track_changes(old_cards, trello_cards)
        if changes:
            update_change_log(service, changes)

        format_first_row(service)

        # Update old_cards to the new state for the next iteration
        old_cards = trello_cards

        sleep(10)  # Adjust sleep time as needed

if __name__ == "__main__":
    sync_data()
