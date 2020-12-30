const express = require('express');
const router = express.Router();
const axios = require('axios').default;

router.get('/', async (req, res) => {
    const connections = JSON.parse(req.query.connections);

    const result = [];
    try {
        for (const connection of connections) {
            const response = await axios.get(`https://timetable.search.ch/api/route.json?num=1&from=${connection[0]}&to=${connection[1]}`);
            const departure = new Date(Date.parse(response.data.connections[0].departure));

            result.push(
                {
                    connection: `${connection[0]} -> ${connection[1]}`,
                    departure: `${departure.getHours()}:${departure.getMinutes()}`,
                    departureFormatted: `${departure.getHours()}:${(departure.getMinutes() < 10 ? '0' : '') + departure.getMinutes()} Uhr`
                }
            );
        }
        
        res.send({connections: result});
    } catch (e) {
        res.status(404).send({
            "error": "no route found"
        })
    }
});

module.exports = router;