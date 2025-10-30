import os
import time
from datetime import datetime
from grow.moisture import Moisture
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Google Sheets API setup ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1fTo3iM-Cx3aHHIhCSZdE_poF8YB6l79xb78klvEHR98'
RANGE_NAME = 'Sheet6!A:D'

BASE_DIR = '/home/jasonvega/Desktop/project'
TOKEN_PATH = os.path.join(BASE_DIR, '/home/jasonvega/Desktop/project/moisture_token.json')
CREDS_PATH = os.path.join(BASE_DIR, '/home/jasonvega/Desktop/project/moisture_credentials.json')

m1 = Moisture(1)
m2 = Moisture(2)
m3 = Moisture(3)

dry_points = [27, 27, 27]
wet_points  = [3, 3, 3]

def moisture_percentage(reading, dry, wet):
    if dry <= wet:
        return 0
    pct = (dry - reading) / (dry - wet) * 100
    return max(0, min(100, pct))

def get_sheets_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

def main():
    _ = [m.moisture for m in (m1, m2, m3)] 
    time.sleep(2.0)  
    _ = [m.moisture for m in (m1, m2, m3)]   

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    r1, r2, r3 = m1.moisture, m2.moisture, m3.moisture
    pct1 = moisture_percentage(r1, dry_points[0], wet_points[0])
    pct2 = moisture_percentage(r2, dry_points[1], wet_points[1])
    pct3 = moisture_percentage(r3, dry_points[2], wet_points[2])

    print(f"{timestamp} | Moisture:   1 = {pct1:.1f}%   2 = {pct2:.1f}%   3 = {pct3:.1f}%")

    try:
        sheets_service = get_sheets_service()
        values = [[timestamp, f"{pct1:.1f}", f"{pct2:.1f}", f"{pct3:.1f}"]]
        body = {'values': values}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        print("✅ Moisture data uploaded successfully!")
    except HttpError as e:
        print(f"❌ Google Sheets upload failed: {e}")

if __name__ == '__main__':
    main()
