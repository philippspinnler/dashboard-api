import httpx
import locale
from datetime import datetime, timedelta, time

from icalendar import Calendar
from dateutil.rrule import rrulestr
import pytz
from app import config

local_time_zone = pytz.timezone("Europe/Zurich")
locale.setlocale(locale.LC_TIME, "de_CH.UTF-8")


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
    today = local_time_zone.localize(datetime.combine(today_no_tz, time.min))
    three_days_later_no_tz = today_no_tz + timedelta(days=3)
    three_days_later = local_time_zone.localize(datetime.combine(three_days_later_no_tz, time.max))

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


def group_events_by_day(events):
    grouped_events = []
    today = datetime.now(local_time_zone).date()  # Get today's date in the local timezone
    tomorrow = today + timedelta(days=1)  # Get tomorrow's date

    # Dictionary to temporarily store events grouped by date
    temp_grouped_events = {}

    for event in events:
        event_date = event["start_date"].date()

        # Check if the event date is today, tomorrow, or another day
        if event_date == today:
            event_day = "Heute"
        elif event_date == tomorrow:
            event_day = "Morgen"
        else:
            event_day = event["start_date"].strftime("%A")  # Day name in German

        # Add event to the corresponding day group
        if event_date not in temp_grouped_events:
            temp_grouped_events[event_date] = {"day": event_day, "date": event_date.strftime("%Y-%m-%d"), "events": []}

        temp_grouped_events[event_date]["events"].append(event)

    # Convert the temporary dictionary to a list of dictionaries
    for date, day_info in temp_grouped_events.items():
        grouped_events.append(day_info)

    return grouped_events


def handle_birthdays(events):
    new_events = []
    for event in events:
        age = None
        birthday = False

        summary = event["summary"]

        if summary.startswith("Geburtstag"):
            birthday = True

            # Remove "Geburtstag " and extract the name part
            name_part = summary[11:].strip()

            # Extract the year part from the name_part
            parts = name_part.split()
            year_part = parts[-1]

            # Remove the year from the name_part to clean the summary
            name_without_year = " ".join(parts[:-1])
            summary = f"Geburtstag {name_without_year}"

            try:
                year = int(year_part)

                # If it's a 2-digit year, assume it's in the 1900s (e.g., 85 -> 1985)
                if year < 100:
                    year += 1900

                # Calculate the age based on the current year
                current_year = datetime.now().year
                age = current_year - year
            except ValueError:
                age = None
        else:
            birthday = False

        event["summary"] = summary
        event["birthday"] = birthday
        event["age"] = age

        new_events.append(event)

    return new_events


def get_events():
    calendars = config.get_attribute(["calendars"])

    all_events = []
    for calendar in calendars:
        events = get_events_from_url(
            url=calendar.get("icalUrl"), name=calendar.get("name"), color=calendar.get("color")
        )
        all_events.extend(events)

    # Handle birthdays
    all_events = handle_birthdays(all_events)

    # Sort events by start_date
    sorted_list_of_dicts = sorted(all_events, key=lambda x: x["start_date"])

    # Group the sorted events by day
    grouped_events = group_events_by_day(sorted_list_of_dicts)

    return grouped_events
