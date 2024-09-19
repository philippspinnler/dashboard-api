from urllib.parse import urlencode, urlparse
from fastapi import HTTPException, Response
import httpx
from soco.discovery import by_name
import re
from app import config


def get_data():
    for device in config.get_attribute(["sonos", "devices"]):
        device = by_name(device)
        current_transport = device.get_current_transport_info()
        if current_transport["current_transport_state"] == "PLAYING":
            break
    current_track = device.get_current_track_info()
    current_media = device.get_current_media_info()

    artist = None
    song = None
    image = None
    is_playing_tv = False

    base_url = config.get_attribute(["base_url"])

    if device.is_playing_radio:
        artist = current_media["channel"]
        song = current_track["title"]

        sid_match = re.search(r"sid=([^\&]+)", current_media["uri"])

        if sid_match:
            sid = sid_match.group(1)
            image = f"https://cdn-profiles.tunein.com/{sid}/images/logoq.jpg"
        else:
            image = None
    elif device.is_playing_tv:
        is_playing_tv = True
        artist = "Fernseher"
        song = "HDMI eARC"
        image = f"{base_url}/static/tv.jpg"
    else:
        artist = current_track["artist"]
        song = current_track["title"]
        encoded_album_art = urlencode({"url": current_track["album_art"]})
        image = f"{base_url}/sonos/image-proxy/?{encoded_album_art}"

    playing = {
        "artist": artist,
        "song": song,
        "playing": current_transport["current_transport_state"] == "PLAYING",
        "image": image,
        "is_playing_tv": is_playing_tv,
    }

    return playing


def proxy(url: str):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ["http", "https"]:
        raise HTTPException(status_code=400, detail="Invalid URL scheme. Only 'http' and 'https' are supported.")

    try:
        response = httpx.get(url)
    except httpx.RequestError:
        raise HTTPException(status_code=400, detail="Failed to fetch the URL.")

    if response.status_code == 200:
        return Response(content=response.content, media_type=response.headers.get("content-type"))
    else:
        raise HTTPException(status_code=response.status_code, detail="Image not found or inaccessible.")
