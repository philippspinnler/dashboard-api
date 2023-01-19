const express = require('express');
const router = express.Router();
const axios = require('axios').default;

const departures = {};

router.get('/', async (req, res) => {
    const connections = JSON.parse(req.query.connections);

    const result = [];
    try {
        for (const connection of connections) {
            const connectionName = `${connection[0]} -> ${connection[1]}`;

            if (departures[connectionName]) {
                const departureDate = new Date(departures[connectionName].departure);
                if (departureDate > new Date()) {
                    result.push(departures[connectionName]);
                    continue;
                }
            }

            const from = encodeURIComponent(connection[0]);
            const to = encodeURIComponent(connection[1]);

            const response = await axios.get(`https://timetable.search.ch/api/route.json?num=2&from=${from}&to=${to}${connection[2] == 'direct' ? '&direct=1' : ''}`);

            let departure;

            for (const connection_response of response.data.connections) {
                if (connection_response.legs && connection_response.legs.filter(leg => leg.hasOwnProperty('type') && leg.type.toLowerCase() != 'walk').length > 0) {
                    departure = new Date(connection_response.departure);
                    break;
                }
            }

            if (!departure) {
                departures[connectionName] = {}
            } else {
                departures[connectionName] = {
                    connection: connectionName,
                    departure: `${departure.toISOString()}`,
                    departureHHMM: `${departure.getHours()}:${departure.getMinutes()}`,
                    departureFormatted: `${departure.getHours()}:${(departure.getMinutes() < 10 ? '0' : '') + departure.getMinutes()} Uhr`
                };
            }

            result.push(
                departures[connectionName]
            );
        }

        res.send({ connections: result });
    } catch (e) {
        res.status(404).send({
            "error": `no route found (${e})`
        })
    }
});

module.exports = router;