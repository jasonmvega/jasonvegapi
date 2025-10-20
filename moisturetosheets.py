import time
import datetime
import os

from grow.moisture import Moisture
import RPi.GPIO as GPIO

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# ------------------------------------
# CONFIGURATION
# ------------------------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1fTo3iM-Cx3aHHIhCSZdE_poF8YB6l79xb78klvEHR98'  # <-- paste from Google Sheets URL
RANGE_NAME = 'Sheet6!A:D'
CREDENTIALS_FILE = '/home/jasonvega/Desktop/project/moisture_credentials.json'
TOKEN_FILE = '/home/jasonvega/Desktop/project/moisture_token.json'

# Moisture calibration values (update these based on your sensor calibration!)
MOISTURE_MIN = 300  # Dry value
MOISTURE_MAX = 800  # Wet value

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
# MOISTURE TO PERCENTAGE
# ------------------------------------
def moisture_to_percent(value):
    # Clamp value between min and max
    value = max(MOISTURE_MIN, min(MOISTURE_MAX, value))
    # Map to percentage (0 = dry, 100 = wet)
    percent = int(round((value - MOISTURE_MIN) / (MOISTURE_MAX - MOISTURE_MIN) * 100))
    return percent

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
# ONE-SHOT DATA COLLECTION FOR CRON
# ------------------------------------
def main():
    service = get_service()

    # Create sensor objects ONCE for each channel
    sensor1 = Moisture(channel=1)
    sensor2 = Moisture(channel=2)
    sensor3 = Moisture(channel=3)

    try:
        # Wait for sensors to get an accurate reading
        print("Initializing sensors, waiting for accurate readings...")
        time.sleep(2)

        # Discard first readings (often zero on startup)
        _ = [sensor1.moisture, sensor2.moisture, sensor3.moisture]
        time.sleep(1)  # Give it a little more time for first "real" pulses

        readings = [sensor1.moisture, sensor2.moisture, sensor3.moisture]
        readings_percent = [moisture_to_percent(r) for r in readings]

        # Only upload if at least one reading is nonzero (optional safeguard)
        if any(r > 0 for r in readings):
            append_to_sheet(service, readings)
            print(f"{datetime.datetime.now()} → Uploaded moisture data: {readings}")
            print(f"Readings as percentage: {readings_percent[0]}%, {readings_percent[1]}%, {readings_percent[2]}%")
        else:
            print(f"{datetime.datetime.now()} → Skipped upload: sensor readings are zero ({readings})")
    finally:
        # --- Clean up GPIO interrupts before exit ---
        GPIO.cleanup()

if __name__ == '__main__':
    main()
