def list_albums():
    creds = google_auth()
    url = "https://photoslibrary.googleapis.com/v1/albums?pageSize=50"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        albums = response.json().get("albums", [])
        for a in albums:
            print(f"{a['title']}  ->  {a['id']}")
    else:
        print("❌ Could not list albums:", response.text)

list_albums()
