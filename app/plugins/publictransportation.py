from fastapi import HTTPException
import httpx
from datetime import datetime
import json
from urllib.parse import quote


def get_data(connections: str):
    departures = {}

    try:
        connections_list = json.loads(connections)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    result = []

    for connection in connections_list:
        if len(connection) < 3:
            raise HTTPException(status_code=400, detail="Each connection must have three elements")

        from_location = connection[0]
        to_location = connection[1]
        connection_type = connection[2]

        connection_name = f"{from_location} -> {to_location}"

        if connection_name in departures:
            departure_date = datetime.fromisoformat(departures[connection_name]["departure"])
            if departure_date > datetime.now():
                result.append(departures[connection_name])
                continue

        from_encoded = quote(from_location)
        to_encoded = quote(to_location)
        direct_param = "&direct=1" if connection_type == "direct" else ""

        try:
            url = f"https://timetable.search.ch/api/route.json?num=2&from={from_encoded}&to={to_encoded}{direct_param}"
            response = httpx.get(url)
            response.raise_for_status()

            data = response.json()
            departure = None

            for connection_response in data.get("connections", []):
                if "legs" in connection_response and any(
                    leg.get("type", "").lower() != "walk" for leg in connection_response["legs"]
                ):
                    departure = datetime.fromisoformat(connection_response["departure"])
                    break

            if not departure:
                departures[connection_name] = {}
            else:
                departures[connection_name] = {
                    "connection": connection_name,
                    "departure": departure.isoformat(),
                    "departureHHMM": departure.strftime("%H:%M"),
                    "departureFormatted": departure.strftime("%H:%M Uhr"),
                }

            result.append(departures[connection_name])

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=404, detail=f"no route found ({e})")

    return {"connections": result}
