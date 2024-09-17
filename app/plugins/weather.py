import httpx
from datetime import datetime
import pytz
from app import config


def get_data(lat: float = 47.4176969, lon: float = 7.7612123):
    units = "metric"
    lang = "de"
    exclude = "minutely,hourly,alerts"
    api_key = config.get_attribute(["weather", "api_key"])

    url = (
        f"https://api.openweathermap.org/data/3.0/onecall?"
        f"lat={lat}&lon={lon}&exclude={exclude}&appid={api_key}"
        f"&units={units}&lang={lang}"
    )

    response = httpx.get(url)
    data = response.json()

    current_weather = {
        "temperature": data["current"]["temp"],
        "temperatureFeelsLike": data["current"]["feels_like"],
        "weather": [
            {"id": weather["id"], "icon": weather["icon"], "description": weather["description"]}
            for weather in data["current"]["weather"]
        ],
    }

    daily_weather = [
        {
            "date": datetime.fromtimestamp(day["dt"], pytz.UTC).isoformat(),
            "temperature": {"min": day["temp"]["min"], "max": day["temp"]["max"]},
            "weather": [
                {"id": weather["id"], "icon": weather["icon"], "description": weather["description"]}
                for weather in day["weather"]
            ],
        }
        for day in data["daily"]
    ]

    return {"current": current_weather, "daily": daily_weather}
