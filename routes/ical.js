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
    const howManyDays = 4;
    const calendars = JSON.parse(process.env.MODULE_ICAL_CALENDARS);

    let allEvents = [];
    for (const calendar of calendars) {
        const events = await getDaysFromIcal(calendar, howManyDays);
        allEvents = [...allEvents, ...events];
    }
    
    allEvents = allEvents.sort((a, b) => a.start - b.start);
   
    const grouppedEvents = [];
    for (const event of allEvents) {
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
    
    res.send({
        groupped: grouppedEvents.slice(0, howManyDays)
    });
});

module.exports = router;

function isExcludedDate(event, date) {
    let excluded = false;

    if (event.exdate) {
        for (const exdate of event.exdate) {
            if (exdate.isSame(date, 'day')) {
                excluded = true;
                break;
            }
        }
    }

    return excluded;
}

async function getDaysFromIcal(calendar, howManyDays=1) {
    const days = [];
    for (let x = 0; x <= howManyDays+3; x++) {
        days.push(dayjs().add(x, 'day'));
    }

    const events = await getIcalFromUrl(calendar.icalUrl);

    const recurringEvents = [];
    let filteredEvents = events.filter(event => {
        let pick = false;

        for (const currentDay of days) {
            if (event.start.isSame(currentDay, 'day') && !event.rrule) {
                pick = true;
            }

            if (event.start.isSameOrBefore(currentDay, 'day') && event.rrule && (!event.rrule.until || event.rrule.until.isSameOrAfter(currentDay, 'day'))) {
                if (event.rrule.freq == 'DAILY') {
                    let newStart = currentDay.set('hour', event.start.get('hour')).set('minute', event.start.get('minute')).set('second', event.start.get('second'));
                    if (!isExcludedDate(event, newStart)) {
                        recurringEvents.push({ ...event, start: newStart });
                    }
                }
                else if (event.rrule.freq == 'WEEKLY') {
                    if (event.start.day() == currentDay.day()) {
                        let newStart = currentDay.set('hour', event.start.get('hour')).set('minute', event.start.get('minute')).set('second', event.start.get('second'));
                        if (!isExcludedDate(event, newStart)) {
                            recurringEvents.push({ ...event, start: newStart });
                        }
                    }
                }
                else if (event.rrule.freq == 'MONTHLY') {
                    if (event.start.date() == currentDay.date()) {
                        let newStart = currentDay.set('hour', event.start.get('hour')).set('minute', event.start.get('minute')).set('second', event.start.get('second'));
                        if (!isExcludedDate(event, newStart)) {
                            recurringEvents.push({ ...event, start: newStart });
                        }
                    }
                }
                else if (event.rrule.freq == 'YEARLY') {
                    if (event.start.get('date') == currentDay.get('date') && event.start.get('month') == currentDay.get('month')) {
                        let newStart = currentDay.set('hour', event.start.get('hour')).set('minute', event.start.get('minute')).set('second', event.start.get('second'));
                        if (!isExcludedDate(event, newStart)) {
                            recurringEvents.push({ ...event, start: newStart });
                        }
                    }
                }
            }
        }

        return pick;
    });

    filteredEvents = filteredEvents.concat(recurringEvents);
    return filteredEvents.map(event => {
        return {
            summary: event.summary,
            start: event.start,
            calendarName: calendar.name,
            color: calendar.color,
            allDay: event.allDay || false
        }
    });
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
        if (event.rrule && event.rrule.count) {
            if (event.rrule.freq == 'DAILY') {
                event.rrule.until = event.start.add(event.rrule.count, 'day');
            } else if (event.rrule.freq == 'WEEKLY') {
                event.rrule.until = event.start.add(event.rrule.count, 'week');
            } else if (event.rrule.freq == 'MONTHLY') {
                event.rrule.until = event.start.add(event.rrule.count, 'month');
            } else if (event.rrule.freq == 'YEARLY') {
                event.rrule.until = event.start.add(event.rrule.count, 'year');
            }
        }

        return event;
    });
}