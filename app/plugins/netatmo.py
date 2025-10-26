import httpx
from app import config

API_URL = "https://api.netatmo.com/api/getstationsdata"
TOKEN_URL = "https://api.netatmo.com/oauth2/token"
DEVICE_ID = config.get_attribute(["netatmo", "device_id"])
CLIENT_ID = config.get_attribute(["netatmo", "client_id"])
CLIENT_SECRET = config.get_attribute(["netatmo", "client_secret"])
OUTDOOR_MODULE_INDEX = config.get_attribute(["netatmo", "outdoor_module_index"])


async def get_data():
    access_token = config.get_attribute(["netatmo", "access_token"])
    refresh_token = config.get_attribute(["netatmo", "refresh_token"])

    if not access_token:
        return missing_auth_response()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}?device_id={DEVICE_ID}&get_favorites=false",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code == 403:
        if await renew_token(refresh_token):
            return await get_data()
        else:
            return auth_error_response()

    return extract_data(response)


async def renew_token(refresh_token):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )

    if response.status_code == 200:
        tokens = response.json()
        update_tokens(tokens["access_token"], tokens["refresh_token"])
        return True
    else:
        clear_tokens()
        print("Error while refreshing token")
        return False


def extract_data(response):
    data = response.json()["body"]["devices"][0]
    indoor_temperature = data["dashboard_data"]["Temperature"]
    indoor_co2 = data["dashboard_data"]["CO2"]
    outdoor_temperature = data["modules"][OUTDOOR_MODULE_INDEX]["dashboard_data"]["Temperature"]

    return {
        "indoor_temperature": indoor_temperature,
        "indoor_co2": indoor_co2,
        "outdoor_temperature": outdoor_temperature,
    }


def missing_auth_response():
    return {
        "indoor_temperature": "missing authentication",
        "indoor_co2": "missing authentication",
        "outdoor_temperature": "missing authentication",
    }


def auth_error_response():
    return {
        "indoor_temperature": "authentication error",
        "indoor_co2": "authentication error",
        "outdoor_temperature": "authentication error",
    }


def update_tokens(access_token, refresh_token):
    config.update_attribute(["netatmo", "access_token"], access_token)
    config.update_attribute(["netatmo", "refresh_token"], refresh_token)


def clear_tokens():
    config.update_attribute(["netatmo", "access_token"], None)
    config.update_attribute(["netatmo", "refresh_token"], None)
