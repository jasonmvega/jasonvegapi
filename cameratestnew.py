from picamera2 import Picamera2
from time import sleep
from datetime import datetime
import os
import requests

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Paths
CREDENTIALS_PATH = "/home/jasonvega/Desktop/project/photos_credentials.json"
TOKEN_PATH = "/home/jasonvega/Desktop/project/photos_token.json"

# Google Photos scopes: upload + album create
SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary.appendonly',
    'https://www.googleapis.com/auth/photoslibrary'
]

def google_auth():
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
    return creds

def create_album(creds, album_name):
    """Always create a new album"""
    create_url = "https://photoslibrary.googleapis.com/v1/albums"
    headers = {"Authorization": f"Bearer {creds.token}"}
    payload = {"album": {"title": album_name}}

    response = requests.post(create_url, headers=headers, json=payload)
    if response.status_code == 200:
        album = response.json()
        print(f"📂 Created new album '{album_name}' with ID {album['id']}")
        return album["id"]
    else:
        print("❌ Album creation failed:", response.text)
        return None

def upload_to_new_album(file_path, album_name):
    creds = google_auth()

    # Step 1: Upload file → uploadToken
    upload_url = "https://photoslibrary.googleapis.com/v1/uploads"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-type": "application/octet-stream",
        "X-Goog-Upload-File-Name": os.path.basename(file_path),
        "X-Goog-Upload-Protocol": "raw",
    }

    with open(file_path, "rb") as f:
        response = requests.post(upload_url, data=f, headers=headers)

    if response.status_code != 200:
        print("❌ Upload step failed:", response.text)
        return

    upload_token = response.content.decode("utf-8")

    # Step 2: Create a brand-new album
    album_id = create_album(creds, album_name)
    if not album_id:
        return

    # Step 3: Add photo into new album
    create_url = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
    payload = {
        "albumId": album_id,
        "newMediaItems": [
            {
                "description": f"Photo from {album_name}",
                "simpleMediaItem": {"uploadToken": upload_token}
            }
        ]
    }

    response = requests.post(create_url, headers={"Authorization": f"Bearer {creds.token}"}, json=payload)

    if response.status_code == 200:
        print(f"✅ Uploaded photo into new album '{album_name}'")
    else:
        print("❌ Media creation failed:", response.text)


# ---- Camera section (Picamera2 instead of PiCamera) ----
picam2 = Picamera2()
config = picam2.create_still_configuration()  # highest resolution still capture
picam2.configure(config)

picam2.start()
sleep(2)  # let the camera adjust exposure etc.

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f'/home/jasonvega/Desktop/image_{timestamp}.jpg'

picam2.capture_file(file_path)
picam2.stop()

print(f"📷 Saved photo: {file_path}")

# Album name = timestamp (so each photo has its own album)
upload_to_new_album(file_path, f"Photo_{timestamp}")
