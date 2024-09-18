import re
import httpx
from app import config


def get_data():
    client_key = config.get_attribute(["eoguide", "client_key"])
    username = config.get_attribute(["eoguide", "username"])
    password = config.get_attribute(["eoguide", "password"])

    response = httpx.get(
        f"https://api.appfigures.com/v2/reports/sales/?client_key={client_key}", auth=(username, password)
    )
    response.raise_for_status()  # Raise error if request fails
    sales_data = response.json()

    response_review = httpx.get(
        f"https://api.appfigures.com/v2/reviews/?count=1&client_key={client_key}", auth=(username, password)
    )
    response_review.raise_for_status()  # Raise error if request fails
    review_data = response_review.json()

    review = review_data["reviews"][0]
    total = sales_data["downloads"]
    total_formatted = "{:,}".format(total).replace(",", "'")

    review_text = review["review"]
    review_formatted = re.sub(r"([\uE000-\uF8FF]|\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDDFF])", "", review_text).strip()
    stars = float(review["stars"])
    stars_formatted = round(stars * 10) / 10

    return {
        "total": total,
        "totalFormatted": total_formatted,
        "latestReview": {
            "review": review_text,
            "reviewFormatted": review_formatted,
            "stars": stars,
            "starsFormatted": stars_formatted,
        },
    }
