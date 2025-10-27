import asyncio
import httpx
from app import config


async def get_data():
    client_key = config.get_attribute(["eoguide", "client_key"])
    username = config.get_attribute(["eoguide", "username"])
    password = config.get_attribute(["eoguide", "password"])

    # Create client with longer timeout
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(auth=(username, password), timeout=timeout) as client:
        # Make all API calls concurrently for better performance
        responses = await asyncio.gather(
            client.get(
                f"https://api.appfigures.com/v2/reports/sales/?start_date=-1&client_key={client_key}"
            ),
            client.get(
                f"https://api.appfigures.com/v2/reports/sales/?start_date=-30&client_key={client_key}"
            ),
            client.get(
                f"https://api.appfigures.com/v2/reports/sales/?client_key={client_key}"
            ),
            client.get(
                f"https://api.appfigures.com/v2/reports/ratings/?client_key={client_key}"
            ),
        )

        # Check for errors and parse responses
        for response in responses:
            response.raise_for_status()

        sales_24h = responses[0].json()
        sales_30d = responses[1].json()
        sales_total = responses[2].json()
        rating_data = responses[3].json()

    return {
        "net_downloads": {
            "last_24h": sales_24h["net_downloads"],
            "last_30_days": sales_30d["net_downloads"],
            "total": sales_total["net_downloads"],
        },
        "overall_rating": float(rating_data["average"]),
    }
