const express = require('express');
const router = express.Router();
const dayjs = require('dayjs');
const customParseFormat = require('dayjs/plugin/customParseFormat');
dayjs.extend(customParseFormat);
const isSameOrAfter = require('dayjs/plugin/isSameOrAfter');
dayjs.extend(isSameOrAfter);
var isSameOrBefore = require('dayjs/plugin/isSameOrBefore');
dayjs.extend(isSameOrBefore)
const { default: axios } = require('axios');

router.get('/', async (req, res) => {
    const calendars = JSON.parse(process.env.MODULE_ICAL_CALENDARS);
    const howManyDays = 4;
    let allEvents = [];

    for (const calendar of calendars) {
        let events = await getEventsFromURL(calendar.icalUrl);
        events = simplifyEvents(events);

        // we filter here but preserve all rrule events - this filter should reduce the memory usage
        events = filterEventsInThePast(events, {preserveRruleEvents: true});
        events = filterEventsInTheFuture(events, {startDayMoreThanDaysInTheFuture: howManyDays, preserveRruleEvents: true});
        
        events = flattenRruleEvents(events);
        events = removeEventsWithRruleUntilInThePast(events, howManyDays);

        events = filterExcludedDates(events);

        // after flatten the rrule events we have to filter again
        events = filterEventsInThePast(events);
        events = filterEventsInTheFuture(events, {startDayMoreThanDaysInTheFuture: howManyDays});

        events = tagEvents(events, calendar.name);
        events = colorEvents(events, calendar.color);
       
        allEvents = [...allEvents, ...events];
    }

    allEvents = sortEventsByStart(allEvents);
    allEvents = simplifyEventsForReponse(allEvents);
    grouppedEvents = groupEventsByDay(allEvents);

    res.send({
        groupped: grouppedEvents
    });
});

module.exports = router;

async function getEventsFromURL(url) {
    return await getIcalFromUrl(url);
}

function simplifyEvents(events) {
    return events.map(event => simplifyEvent(event));
}

function simplifyEvent(event) {
    return {
        summary: event.summary,
        start: event.start,
        end: event.end,
        rrule: event.rrule,
        allDay: event.allDay || false,
        rawEvent: event,
        exdate: event.exdate,
        calendarName: event.calendarName,
        color: event.color
    }
}

function simplifyEventsForReponse(events) {
    return events.map(event => simplifyEventForResponse(event));
}

function simplifyEventForResponse(event) {
    return {
        summary: event.summary,
        start: event.start,
        end: event.end,
        allDay: event.allDay || false,
        calendarName: event.calendarName,
        color: event.color
    }
}

function tagEvents(events, calendarName) {
    return events.map(event => {
        return {
            ...event,
            calendarName
        }
    });
}

function colorEvents(events, color) {
    return events.map(event => {
        return {
            ...event,
            color
        }
    });
}

function filterEventsInThePast(events, options={}) {
    if (options.preserveRruleEvents) {
        return events.filter(event => event.end > dayjs().startOf('day') || event.rrule);
    }
    return events.filter(event => event.end > dayjs().startOf('day'));
}

function filterEventsInTheFuture(events, options={}) {
    if (options.preserveRruleEvents) {
        return events.filter(event => event.start < dayjs().add(options.startDayMoreThanDaysInTheFuture, 'day').endOf('day') || event.rrule);
    }
    return events.filter(event => event.start < dayjs().add(options.startDayMoreThanDaysInTheFuture, 'day').endOf('day'));
}

function flattenRruleEvents(events) {
    return events.flatMap(event => {
        if (!event.rrule) return [event];

        let unit;
        const newEvents = [];
        if (event.rrule.freq == 'DAILY') {
            unit = 'day';
        } else if (event.rrule.freq == 'WEEKLY') {
            unit = 'week';
        } else if (event.rrule.freq == 'MONTHLY') {
            unit = 'month';
        } else if (event.rrule.freq == 'YEARLY') {
            unit = 'year';
        }

        let countReached = false;
        let count = 1;
        while(event.end < dayjs().add(2, 'year') && !countReached) {
            newEvents.push(simplifyEvent(event));
            const interval = (event.rrule.interval) ? event.rrule.interval : 1;
            if (event.rrule.count) {
                count++;
                if (count > parseInt(event.rrule.count)) {
                    countReached = true;
                }
            }
            event.start = event.start.add(interval, unit);
            event.end = event.end.add(interval, unit);
        }

        blubb = 1;
        return newEvents;
    });
}

function filterExcludedDates(events) {
    return events.filter(event => {
        if (!event.exdate) return true;
        let isExcluded = false;
        for (const excludedDate of event.exdate) {
            blubb = 1;
            if (excludedDate.isSame(event.start, 'day')) {
                isExcluded = true;
                break;
            }
        }
        return isExcluded ? false : true;
    });
}

function removeEventsWithRruleUntilInThePast(events,) {
    return events.filter(event => {
        if (!event.rrule) return true;
        if (!event.rrule.until) return true;
        // ignore until if count is set
        if (event.rrule.until && event.rrule.count) return true;
        if (event.rrule.until < event.start) return false;
        return true;
    });
}

function sortEventsByStart(events) {
    return events.sort((a, b) => a.start - b.start);
}

function groupEventsByDay(events) {
    const grouppedEvents = [];
    for (const event of events) {
        const date = event.start.startOf('day').toISOString();
        const index = grouppedEvents.findIndex(group => group.date == date);
        if (!grouppedEvents[index]) {
            grouppedEvents.push({
                date,
                events: [event]
            });
        } else {
            grouppedEvents[index].events.push(event);
        }
    }

    return grouppedEvents;
}

async function getIcalFromUrl(url) {
    const rawResponse = await axios.get(url);
    const rawCalendarEntries = rawResponse.data.split('\r\n');

    const events = [];
    let isEventActive = false;
    let activeEvent = {};

    function snakeCaseToCamelCase(input) {
        const keyArray = input.split('-');
        let key = keyArray.map(k => k.toLowerCase().charAt(0).toUpperCase() + k.toLowerCase().slice(1)).join('');
        return key.charAt(0).toLowerCase() + key.slice(1);
    }

    function convertICalDate(input) {
        if (input.length > 8) {
            return dayjs(input.replace('T', '').replace('Z', ''), "YYYYMMDDHHmmss");
        }
        return dayjs(input, "YYYYMMDD");
    }

    for (const rawCalendarEntry of rawCalendarEntries) {
        if (rawCalendarEntry != "BEGIN:VEVENT" && !isEventActive) {
            continue;
        }

        isEventActive = true;

        if (rawCalendarEntry == "BEGIN:VEVENT" || rawCalendarEntry == "END:VEVENT") {
            activeEvent['type'] = 'VEVENT';
        } else {
            const splittedRawEntry = rawCalendarEntry.split(':');

            let key = snakeCaseToCamelCase(splittedRawEntry[0]);
            key = key.split(';')[0];

            let value;
            if (key == 'rrule') {
                const valueArray = splittedRawEntry[1].split(';');
                value = {};
                valueArray.map(v => value[snakeCaseToCamelCase(v.split('=')[0])] = v.split('=')[1]);
            }
            else {
                value = splittedRawEntry.slice(1).join('');
            }

            if (key == 'dtstart' && value.length <= 8) {
                activeEvent['allDay'] = true;
            }

            if (['created', 'lastModified', 'dtend', 'dtstamp', 'dtstart', 'exdate'].includes(key)) {
                value = convertICalDate(value);
            }

            if (['dtend', 'dtstamp', 'dtstart'].includes(key)) {
                key = key.slice(2);
            }

            if (key == 'rrule' && value['until']) {
                value['until'] = convertICalDate(value['until']);
            }

            if (key == 'exdate') {
                if (!activeEvent[key]) activeEvent[key] = [];
                activeEvent[key].push(value);
            } else {
                activeEvent[key] = value;
            }
        }

        if (rawCalendarEntry == "END:VEVENT") {
            events.push(activeEvent);
            activeEvent = {};
            isEventActive = false;
        }
    }

    return events.map(event => {
        return event;
    });
}