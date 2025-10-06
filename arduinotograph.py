#!/usr/bin/env python3
import os
import json
import serial
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ====== CONFIG ======
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1fTo3iM-Cx3aHHIhCSZdE_poF8YB6l79xb78klvEHR98'
RANGE_NAME = 'Sheet5!A:D'  # timestamp, sensor, value, unit
BASE_DIR = "/home/jasonvega/project"
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
# ====================


def get_sheets_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)


def main():
    # Setup serial
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)
    sheets_service = get_sheets_service()

    values = []
    timestamp = datetime.datetime.now().isoformat()

    # Read until we have both UV and Temperature (or max 10 lines to avoid hanging)
    sensors_needed = {"UV", "AmbientTemp"}
    sensors_seen = set()

    for _ in range(10):
        line = ser.readline().decode("utf-8").strip()
        if line.startswith("~{"):
            try:
                data = json.loads(line.strip("~|"))
                if data["sensorName"] in sensors_needed:
                    values.append([timestamp, data["sensorName"], data["value"], data["unit"]])
                    sensors_seen.add(data["sensorName"])
                if sensors_seen == sensors_needed:
                    break
            except Exception as e:
                print("Parse error:", line, e)

    # Upload if we got any data
    if values:
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()
        print("Logged:", values)
    else:
        print("No valid sensor data found")


if __name__ == "__main__":
    main()
