import httpx
import json
from typing import Dict, Any, List, Union
from app import config

# Static headers
HEADERS = {
    "Origin": "https://www.icloud.com",
    "Accept-Language": "en-US,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    ),
    "Content-Type": "text/plain",
    "Accept": "*/*",
    "Referer": "https://www.icloud.com/sharedalbum/",
    "Connection": "keep-alive",
}

def get_data() -> Dict[str, List[str]]:
    """
    Fetches enriched image URLs from iCloud shared albums.
    :return: A dictionary with a list of image URLs.
    """
    token = config.get_attribute(["icloud_album_id"])
    images = get_images(token)

    urls = [
        max(photo["derivatives"].values(), key=lambda x: x["fileSize"])["url"]
        for photo in images["photos"]
        if "derivatives" in photo
    ]

    return {"images": urls}

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Splits a list into smaller chunks of a specified size.
    :param lst: The list to chunk.
    :param chunk_size: Size of each chunk.
    :return: List of chunks.
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def get_images(token: str) -> Dict[str, Any]:
    """
    Retrieves images and their metadata enriched with URLs.
    :param token: The authentication token.
    :return: A dictionary containing metadata and enriched photos.
    """
    base_url = get_base_url(token)
    redirected_base_url = get_redirected_base_url(base_url, token)
    api_response = get_api_response(redirected_base_url)

    chunks = chunk_list(api_response["photoGuids"], 25)
    all_urls = {guid: url for chunk in chunks for guid, url in get_urls(redirected_base_url, chunk).items()}

    return {
        "metadata": api_response["metadata"],
        "photos": enrich_images_with_urls(api_response, all_urls),
    }

def get_base_url(token: str) -> str:
    """
    Constructs the base URL for accessing shared streams.
    :param token: The authentication token.
    :return: The base URL.
    """
    BASE_62_CHAR_SET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def base62_to_int(value: str) -> int:
        return sum(BASE_62_CHAR_SET.index(char) * (62 ** idx) for idx, char in enumerate(reversed(value)))

    partition = base62_to_int(token[1]) if token[0] == 'A' else base62_to_int(token[1:3])
    base_url = f"https://p{partition:02d}-sharedstreams.icloud.com/{token}/sharedstreams/"
    return base_url

def get_redirected_base_url(base_url: str, token: str) -> str:
    """
    Resolves potential redirections for the base URL.
    :param base_url: The original base URL.
    :param token: The authentication token.
    :return: The redirected URL or the original URL if no redirection occurred.
    """
    url = f"{base_url}webstream"
    response = httpx.post(url, headers=HEADERS, json={"streamCtag": None}, follow_redirects=False)

    if response.status_code == 330:
        new_host = response.json()["X-Apple-MMe-Host"]
        return f"https://{new_host}/{token}/sharedstreams/"

    response.raise_for_status()
    return base_url

def get_api_response(base_url: str) -> Dict[str, Any]:
    """
    Retrieves metadata and photos from the API.
    :param base_url: The API base URL.
    :return: Parsed JSON response containing metadata and photos.
    """
    url = f"{base_url}webstream"
    response = httpx.post(url, headers=HEADERS, json={"streamCtag": None})
    response.raise_for_status()
    data = response.json()

    return {
        "metadata": {
            "streamName": data["streamName"],
            "userFirstName": data["userFirstName"],
            "userLastName": data["userLastName"],
            "streamCtag": data["streamCtag"],
            "itemsReturned": int(data["itemsReturned"]),
            "locations": data["locations"],
        },
        "photoGuids": [photo["photoGuid"] for photo in data["photos"]],
        "photos": {
            photo["photoGuid"]: {
                **photo,
                "batchDateCreated": parse_date(photo["batchDateCreated"]),
                "dateCreated": parse_date(photo["dateCreated"]),
                "height": int(photo["height"]),
                "width": int(photo["width"]),
                "derivatives": [
                    {**value, "fileSize": int(value["fileSize"]), "width": int(value["width"]), "height": int(value["height"])}
                    for value in photo["derivatives"].values()
                ],
            }
            for photo in data["photos"]
        },
    }

def parse_date(date: str) -> Union[str, None]:
    """
    Parses a date string to ensure consistent format.
    :param date: The date string.
    :return: The parsed date or None on failure.
    """
    try:
        return date
    except Exception:
        return None

def get_urls(base_url: str, photo_guids: List[str]) -> Dict[str, str]:
    """
    Retrieves URLs for a batch of photo GUIDs.
    :param base_url: The API base URL.
    :param photo_guids: A list of photo GUIDs.
    :return: A dictionary mapping GUIDs to URLs.
    """
    url = f"{base_url}webasseturls"
    response = httpx.post(url, headers=HEADERS, json={"photoGuids": photo_guids})
    response.raise_for_status()
    return {
        item_id: f"https://{item['url_location']}{item['url_path']}"
        for item_id, item in response.json()["items"].items()
    }

def enrich_images_with_urls(api_response: Dict[str, Any], urls: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Enriches photo metadata with derivative URLs.
    :param api_response: The API response containing photos and metadata.
    :param urls: A dictionary of checksums to URLs.
    :return: A list of enriched photo objects.
    """
    photos = list(api_response["photos"].values())
    enriched_photos = []

    for photo in photos:
        derivatives = {
            str(derivative["height"]): {**derivative, "url": urls[derivative["checksum"]]}
            for derivative in photo["derivatives"]
            if derivative["checksum"] in urls
        }
        enriched_photos.append({**photo, "derivatives": derivatives})

    return enriched_photos
