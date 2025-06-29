import httpx
from app import config

def get_data():
    IMMICH_URL = config.get_attribute(["immich", "url"])
    API_KEY = config.get_attribute(["immich", "api_key"])
    ALBUM_NAME = config.get_attribute(["immich", "album_name"])

    headers = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }

    with httpx.Client(headers=headers) as client:
        # 1. Get all albums
        response = client.get(f"{IMMICH_URL}/api/albums")
        response.raise_for_status()
        albums = response.json()

        # 2. Find album ID
        album = next((a for a in albums if a["albumName"] == ALBUM_NAME), None)
        if not album:
            raise Exception(f"Album '{ALBUM_NAME}' not found")
        album_id = album["id"]

        # 3. Get assets in album
        response = client.get(f"{IMMICH_URL}/api/albums/{album_id}")
        response.raise_for_status()
        assets = response.json().get("assets", [])

        # 4. Build image URLs
        image_urls = [
            f"{IMMICH_URL}/api/assets/{asset['id']}/thumbnail?size=fullsize&key={config.get_attribute(['immich', 'share_key'])}&c={config.get_attribute(['immich', 'c'])}"
            for asset in assets
        ]

    return {"images": image_urls}
