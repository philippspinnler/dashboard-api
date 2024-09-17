from soco.discovery import by_name
import re
from app import config


def get_data():
    device = by_name(config.get_attribute(["sonos", "device_name"]))
    current_track = device.get_current_track_info()
    current_media = device.get_current_media_info()
    current_transport = device.get_current_transport_info()

    artist = None
    song = None
    image = None
    is_playing_tv = False

    if device.is_playing_radio:
        artist = current_media["channel"]
        song = current_track["title"]

        sid_match = re.search(r"sid=([^\&]+)", current_media["uri"])

        if sid_match:
            sid = sid_match.group(1)
            image = f"https://cdn-profiles.tunein.com/{sid}/images/logoq.jpg"
        else:
            image = None
    if device.is_playing_tv:
        is_playing_tv = True
    else:
        artist = current_track["artist"]
        song = current_track["title"]
        image = current_track["album_art"]

    playing = {
        "artist": artist,
        "song": song,
        "playing": current_transport["current_transport_state"] == "PLAYING",
        "image": image,
        "is_playing_tv": is_playing_tv,
    }

    return playing
