import requests
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# Trello API credentials
TRELLO_KEY = 'de191ae0dcf871ec94a2c3a9e301f9ff'
TRELLO_TOKEN = 'ATTAa60e29643e75d864c757c0e614df0174ad436b9dbbbf7f99a36f9c51cf3799be0DD6667E'
BOARD_ID = '5fccc1a892fd80504a4a8781'

# Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '14s7UqY65O6n8U04AcqHlKbkVIJZS1gYyPPDWdHO8u8o'
CREDENTIALS_FILE = 'crested-trainer-292909-509d7f962395.json'

# Authenticate and create the Google Sheets API service
def create_google_sheets_service():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

# Retrieve cards from Trello board
def get_trello_cards():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    query = {
        'key': TRELLO_KEY,
        'token': TRELLO_TOKEN
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch cards: {response.status_code} {response.text}")
        return []

# Retrieve lists from Trello board and map list IDs to names
def get_list_names():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
    query = {
        'key': TRELLO_KEY,
        'token': TRELLO_TOKEN
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        lists = response.json()
        return {lst['id']: lst['name'] for lst in lists}
    else:
        print(f"Failed to fetch lists: {response.status_code} {response.text}")
        return {}

# Retrieve member names from their IDs
def get_member_names(member_ids):
    member_names = []
    for member_id in member_ids:
        url = f"https://api.trello.com/1/members/{member_id}"
        query = {
            'key': TRELLO_KEY,
            'token': TRELLO_TOKEN
        }
        response = requests.get(url, params=query)
        if response.status_code == 200:
            member_data = response.json()
            member_names.append(member_data.get('fullName', 'Unknown'))
    return member_names

# Organize data by lists using list names
def organize_data_by_list(cards, list_names):
    organized_data = {}
    for card in cards:
        list_name = list_names.get(card.get('idList'), 'Unknown List')
        if list_name not in organized_data:
            organized_data[list_name] = []
        organized_data[list_name].append(card)
    return organized_data

# Update Google Sheets with the organized data
def update_google_sheet(service, organized_data):
    headers = list(organized_data.keys())
    values = [headers]
    
    max_cards = max(len(cards) for cards in organized_data.values())
    for i in range(max_cards):
        row = []
        for list_name in headers:
            if i < len(organized_data[list_name]):
                card = organized_data[list_name][i]
                member_names = get_member_names(card.get('idMembers', []))
                row.append(f"{card['name']}\nDescription: {card.get('desc', '')}\n"
                           f"Members: {', '.join(member_names)}\nDue Date: {card.get('due', 'No Due Date')}")
            else:
                row.append('')
        values.append(row)
    
    body = {'values': values}
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range='Sheet1!A1',
            valueInputOption='RAW', body=body).execute()
        print("Google Sheet updated with card data.")
    except HttpError as error:
        print(f"An error occurred: {error}")

# Sync data from Trello to Google Sheets every 5 seconds
def sync_data():
    service = create_google_sheets_service()
    list_names = get_list_names()
    
    while True:
        cards = get_trello_cards()
        if cards:
            organized_data = organize_data_by_list(cards, list_names)
            update_google_sheet(service, organized_data)
        time.sleep(5)  # Wait for 5 seconds before refreshing

# Execute the sync process
if __name__ == "__main__":
    sync_data()
