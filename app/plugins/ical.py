import httpx
from datetime import datetime, timedelta

from dateutil.tz import gettz
from icalendar import Calendar
from dateutil.rrule import rrulestr
import pytz
from app import config

local_time_zone = gettz("Europe/Zurich")


def parse_webcal(url):
    response = httpx.get(url)
    cal = Calendar.from_ical(response.text)
    return cal


def ensure_timezone(dt, timezone_str="CET"):
    if dt.tzinfo is None:
        tz = pytz.timezone(timezone_str)
        dt = tz.localize(dt)

    return dt


def get_events_in_next_days(cal, days=3):
    today_no_tz = datetime.today()
    today = today_no_tz.replace(tzinfo=local_time_zone)
    three_days_later_no_tz = today_no_tz + timedelta(days=days)
    three_days_later = three_days_later_no_tz.replace(tzinfo=local_time_zone)

    events_in_next_three_days = []

    for event in cal.walk("VEVENT"):
        all_day = False
        start_date = event.get("dtstart").dt

        if not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
            all_day = True

        if not start_date.tzinfo:
            start_date = start_date.replace(tzinfo=local_time_zone)

        # Handle recurring events
        rrule_str = event.get("rrule")
        if rrule_str:
            try:
                rrules = rrulestr(rrule_str.to_ical().decode("utf-8"), dtstart=start_date)
                occurrences = rrules.between(today, three_days_later, inc=True)
            except ValueError:
                rrules = rrulestr(
                    rrule_str.to_ical().decode("utf-8"),
                    dtstart=start_date.astimezone(local_time_zone).replace(tzinfo=None),
                )
                occurrences = rrules.between(today_no_tz, three_days_later_no_tz, inc=True)
            for occurrence in occurrences:
                events_in_next_three_days.append(
                    {
                        "summary": event.get("summary").to_ical().decode("utf-8"),
                        "start_date": ensure_timezone(occurrence),
                        "all_day": all_day,
                    }
                )
        else:
            if today <= start_date < three_days_later:
                events_in_next_three_days.append(
                    {
                        "summary": event.get("summary").to_ical().decode("utf-8"),
                        "start_date": ensure_timezone(start_date),
                        "all_day": all_day,
                    }
                )

    return events_in_next_three_days


def get_events_from_url(url, name, color):
    cal = parse_webcal(url)
    events = get_events_in_next_days(cal, days=5)
    events = [{**event, "name": name, "color": color} for event in events]
    return events


def get_events():
    calendars = config.get_attribute(["calendars"])

    all_events = []
    for calendar in calendars:
        events = get_events_from_url(
            url=calendar.get("icalUrl"), name=calendar.get("name"), color=calendar.get("color")
        )
        all_events.extend(events)

    sorted_list_of_dicts = sorted(all_events, key=lambda x: x["start_date"])

    return sorted_list_of_dicts
