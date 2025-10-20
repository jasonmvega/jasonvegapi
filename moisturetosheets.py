#!/usr/bin/env python3
import time
import datetime
import os
import sys

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
# APPEND SATURATION TO SHEETS
# ------------------------------------
def append_saturation_to_sheet(service, sats):
    """
    sats: iterable of 3 saturation floats (0.0 - 1.0)
    Writes timestamp and three saturation percentages to the sheet.
    """
    # Convert to percentage with 2 decimal places
    vals_pct = [round(s * 100.0, 2) if s is not None else None for s in sats]
    values = [[
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        vals_pct[0],
        vals_pct[1],
        vals_pct[2]
    ]]
    body = {'values': values}
    try:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
    except Exception as e:
        # If Sheets fails we still want to cleanup GPIO and exit gracefully
        print(f"Google Sheets append failed: {e}", file=sys.stderr)

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
        # Give sensors time to start counting pulses
        print("Initializing sensors, waiting for accurate readings...")
        time.sleep(2)

        # Discard first readings (often zero on startup)
        _ = [sensor1.moisture, sensor2.moisture, sensor3.moisture]
        time.sleep(1)  # extra small delay for first real pulses

        # Read saturation values (0.0 - 1.0)
        try:
            sat1 = sensor1.saturation
        except Exception:
            sat1 = None
        try:
            sat2 = sensor2.saturation
        except Exception:
            sat2 = None
        try:
            sat3 = sensor3.saturation
        except Exception:
            sat3 = None

        sats = [sat1, sat2, sat3]

        # Optional safeguard: only upload if at least one sensor returned a non-None value
        if any(s is not None for s in sats):
            append_saturation_to_sheet(service, sats)
            print(f"{datetime.datetime.now()} → Uploaded saturation data (percent): {[round(s*100,2) if s is not None else None for s in sats]}")
        else:
            print(f"{datetime.datetime.now()} → Skipped upload: sensor saturations unavailable ({sats})")
    finally:
        # Ensure GPIO state is cleaned up so grow-monitor can start without conflicts
        try:
            GPIO.cleanup()
        except Exception as e:
            # Not critical, but log to stderr
            print(f"GPIO.cleanup() failed: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
