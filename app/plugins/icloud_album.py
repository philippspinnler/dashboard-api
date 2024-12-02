import httpx

from app import config


def get_data():
    album_code = client_key = config.get_attribute(["icloud_album_id"])

    base_url = _get_base_url(album_code)

    webstream_url = f"{base_url}webstream"
    webasseturls_url = f"{base_url}webasseturls"

    x = httpx.post(webstream_url, json={"streamCtag":None})
    webstream_data = x.json()

    if x.status_code == 330:
        new_host = webstream_data.get("X-Apple-MMe-Host")

        base_url = f"https://{new_host}/{album_code}/sharedstreams/"
        webstream_url = f"{base_url}webstream"
        webasseturls_url = f"{base_url}webasseturls"

        x = httpx.post(webstream_url, json={"streamCtag":None})
        webstream_data = x.json()

    photos = []
    for item in webstream_data['photos']:
        photos.append(item['photoGuid'])

    y = httpx.post(webasseturls_url, json={"photoGuids":photos})
    webasset_data = y.json()

    images = []
    for img_key in webasset_data['items'].keys():
        img = webasset_data['items'][img_key]
        image_url = f"https://{img['url_location']}{img['url_path']}"
        images.append(image_url)
    
    return {"images": images}

def _get_base_url(token: str) -> str:
    BASE_62_CHAR_SET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def base62_to_int(e: str) -> int:
        t = 0
        for char in e:
            t = t * 62 + BASE_62_CHAR_SET.index(char)
        return t

    e = token
    t = e[0]
    n = base62_to_int(e[1]) if t == 'A' else base62_to_int(e[1:3])
    i = e.find(';')
    r = e
    s = None

    if i >= 0:
        s = e[i + 1:]
        r = r.replace(';' + s, '')

    server_partition = n

    base_url = 'https://p'
    base_url += f"{server_partition:02d}-sharedstreams.icloud.com"
    base_url += f"/{token}/sharedstreams/"

    return base_url


if __name__ == "__main__":
    get_data()