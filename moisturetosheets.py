
import time
import datetime
import os
from grow.moisture import MoistureSensor
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# ------------------------------------
# CONFIGURATION
# ------------------------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'  # <-- paste from Google Sheets URL
RANGE_NAME = 'Sheet1!A:D'
CREDENTIALS_FILE = '/home/pi/project/credentials.json'
TOKEN_FILE = '/home/pi/project/token.json'

# ------------------------------------
# GOOGLE AUTH SETUP
# ------------------------------------
def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

# ------------------------------------
# READ MOISTURE DATA
# ------------------------------------
def read_moisture():
    sensor = MoistureSensor()
    readings = sensor.read_all()  # returns list of 3 moisture values
    return readings

# ------------------------------------
# APPEND TO SHEETS
# ------------------------------------
def append_to_sheet(service, data):
    values = [[
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        data[0],
        data[1],
        data[2]
    ]]
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

# ------------------------------------
# MAIN LOOP
# ------------------------------------
def main():
    service = get_service()
    while True:
        moisture_data = read_moisture()
        append_to_sheet(service, moisture_data)
        print(f"{datetime.datetime.now()} → Uploaded moisture data: {moisture_data}")
        time.sleep(300)  # every 5 minutes (change as needed)

if __name__ == '__main__':
    main()
