import httpx
import logging

import locale
from datetime import datetime, timedelta, time

from icalendar import Calendar
from dateutil.rrule import rrulestr
import pytz
from app import config

# Configure logging
logger = logging.getLogger(__name__)

local_time_zone = pytz.timezone("Europe/Zurich")
locale.setlocale(locale.LC_TIME, "de_CH.UTF-8")


async def parse_webcal(url):
    """
    Fetch and parse an iCal calendar from a URL.
    Includes robust error handling and validation.
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,  # 30 second timeout
            follow_redirects=True,
            verify=True,  # Verify SSL certificates
        ) as client:
            logger.info(f"Fetching calendar from URL: {url}")
            response = await client.get(url)
            
            # Log response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content-type: {response.headers.get('content-type', 'unknown')}")
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"Failed to fetch calendar from {url}: HTTP {response.status_code}")
                logger.error(f"Response body (first 500 chars): {response.text[:500]}")
                raise ValueError(f"HTTP {response.status_code} error when fetching calendar")
            
            # Validate response content
            response_text = response.text.strip()
            
            if not response_text:
                logger.error(f"Empty response from {url}")
                raise ValueError("Empty calendar response")
            
            # Check if response looks like iCal format
            if not response_text.startswith("BEGIN:VCALENDAR"):
                logger.error(f"Response doesn't appear to be iCal format from {url}")
                logger.error(f"Response starts with: {response_text[:200]}")
                raise ValueError("Response is not in iCal format")
            
            logger.debug(f"Response length: {len(response_text)} characters")
            
            # Parse the calendar
            cal = Calendar.from_ical(response_text)
            logger.info(f"Successfully parsed calendar from {url}")
            return cal
            
    except httpx.TimeoutException as e:
        logger.error(f"Timeout fetching calendar from {url}: {str(e)}")
        raise ValueError(f"Timeout fetching calendar: {str(e)}")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching calendar from {url}: {str(e)}")
        raise ValueError(f"HTTP error fetching calendar: {str(e)}")
    except ValueError as e:
        # Re-raise ValueError with context
        logger.error(f"Validation error for {url}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing calendar from {url}: {str(e)}")
        logger.exception("Full traceback:")
        raise ValueError(f"Failed to parse calendar: {str(e)}")


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
            rrule_text = rrule_str.to_ical().decode("utf-8")
            
            # Fix for yearly recurring events with BYMONTHDAY but no BYMONTH
            # This ensures birthdays and anniversaries recur on the correct month
            if "FREQ=YEARLY" in rrule_text and "BYMONTHDAY=" in rrule_text and "BYMONTH=" not in rrule_text:
                # Extract month from DTSTART to use as the default
                start_month = start_date.month
                # Add BYMONTH to the RRULE to make it explicit
                rrule_text = rrule_text + f";BYMONTH={start_month}"
                logger.debug(f"Added BYMONTH={start_month} to RRULE for event: {event.get('summary')}")
            
            try:
                rrules = rrulestr(rrule_text, dtstart=start_date)
                occurrences = rrules.between(today, three_days_later, inc=True)
            except ValueError:
                rrules = rrulestr(
                    rrule_text,
                    dtstart=start_date.astimezone(local_time_zone).replace(tzinfo=None),
                )
                occurrences = rrules.between(today_no_tz, three_days_later_no_tz, inc=True)
            for occurrence in occurrences:
                events_in_next_three_days.append(
                    {
                        "summary": event.get("summary").to_ical().decode("utf-8"),
                        "start_date": ensure_timezone(occurrence),
                        "start_time": ensure_timezone(occurrence).strftime("%H:%M"),
                        "all_day": all_day,
                    }
                )
        else:
            if today <= start_date < three_days_later:
                events_in_next_three_days.append(
                    {
                        "summary": event.get("summary").to_ical().decode("utf-8"),
                        "start_date": ensure_timezone(start_date),
                        "start_time": ensure_timezone(start_date).strftime("%H:%M"),
                        "all_day": all_day,
                    }
                )

    return events_in_next_three_days


async def get_events_from_url(url, name, color):
    """
    Fetch and process events from a calendar URL.
    Returns empty list on error to allow other calendars to continue processing.
    """
    try:
        cal = await parse_webcal(url)
        events = get_events_in_next_days(cal, days=5)
        events = [{**event, "name": name, "color": color} for event in events]
        logger.info(f"Successfully retrieved {len(events)} events from calendar '{name}'")
        return events
    except Exception as e:
        logger.error(f"Failed to get events from calendar '{name}' ({url}): {str(e)}")
        logger.exception("Full traceback:")
        # Return empty list to allow other calendars to continue
        return []


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
            temp_grouped_events[event_date] = {
                "day": event_day,
                "date": event_date.strftime("%d. %B"),
                "events": [],
            }

        temp_grouped_events[event_date]["events"].append(event)

    # Convert the temporary dictionary to a list of dictionaries
    for date, day_info in temp_grouped_events.items():
        grouped_events.append(day_info)

    return grouped_events


def handle_special_events(events):
    new_events = []
    for event in events:
        years = None
        event_type = None
        summary = event["summary"].strip()

        # Check for birthday (now at the end)
        if summary.endswith(" Geburtstag"):
            event_type = "birthday"
            # Remove " Geburtstag" and extract the name and year part
            name_year_part = summary[:-11].strip()
        # Check for wedding anniversary (now at the end)
        elif summary.endswith(" Hochzeitstag"):
            event_type = "anniversary"
            # Remove " Hochzeitstag" and extract the name and year part
            name_year_part = summary[:-13].strip()
        else:
            # Not a special event
            event["special_event"] = None
            new_events.append(event)
            continue

        # Extract the name and year from name_year_part
        parts = name_year_part.split()

        if len(parts) == 1:
            # If there's only one part, assume it's the name
            name = parts[0]
            years = None
        else:
            # The last part should be the year
            year_part = parts[-1]
            
            # All parts before the year are the name (supports multiple names)
            name = " ".join(parts[:-1])

            try:
                year = int(year_part)

                # If it's a 2-digit year, assume it's in the 1900s (e.g., 85 -> 1985)
                if year < 100:
                    year += 1900

                # Calculate the years based on the current year
                current_year = datetime.now().year
                years = current_year - year
            except ValueError:
                # If year parsing fails, treat all parts as the name
                name = name_year_part
                years = None

        event["special_event"] = {
            "type": event_type,
            "name": name,
            "years": years,
        }

        new_events.append(event)

    return new_events


async def get_events():
    """
    Fetch events from all configured calendars.
    Continues processing even if individual calendars fail.
    """
    calendars = config.get_attribute(["calendars"])
    
    if not calendars:
        logger.warning("No calendars configured")
        return []
    
    logger.info(f"Processing {len(calendars)} calendar(s)")
    
    all_events = []
    successful_calendars = 0
    failed_calendars = 0
    
    for calendar in calendars:
        calendar_name = calendar.get("name", "Unknown")
        calendar_url = calendar.get("icalUrl")
        calendar_color = calendar.get("color", "#000000")
        
        if not calendar_url:
            logger.error(f"Calendar '{calendar_name}' has no URL configured, skipping")
            failed_calendars += 1
            continue
        
        try:
            events = await get_events_from_url(
                url=calendar_url, 
                name=calendar_name, 
                color=calendar_color
            )
            all_events.extend(events)
            
            if events:
                successful_calendars += 1
            else:
                # Empty events could mean error (logged in get_events_from_url) or no events
                logger.warning(f"No events returned from calendar '{calendar_name}'")
                
        except Exception as e:
            logger.error(f"Unexpected error processing calendar '{calendar_name}': {str(e)}")
            logger.exception("Full traceback:")
            failed_calendars += 1
            continue
    
    logger.info(f"Completed processing: {successful_calendars} successful, {failed_calendars} failed, {len(all_events)} total events")
    
    if not all_events:
        logger.warning("No events found from any calendar")
        return []
    
    # Handle special events (birthdays and anniversaries)
    all_events = handle_special_events(all_events)

    # Sort events by start_date
    sorted_list_of_dicts = sorted(all_events, key=lambda x: x["start_date"])

    # Group the sorted events by day
    grouped_events = group_events_by_day(sorted_list_of_dicts)
    
    logger.info(f"Returning {len(grouped_events)} days of events")
    return grouped_events
