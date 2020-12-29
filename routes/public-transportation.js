const express = require('express');
const router = express.Router();
const axios = require('axios').default;

router.get('/', async (req, res) => {
    const from = req.query.from;
    const to = req.query.to;
    try {
        const response = await axios.get(`https://timetable.search.ch/api/route.json?num=1&from=${from}&to=${to}`);
        const departure = new Date(Date.parse(response.data.connections[0].departure));
        res.send({
            departure: `${departure.getHours()}:${departure.getMinutes()}`,
            departureFormatted: `${departure.getHours()}:${(departure.getMinutes() < 10 ? '0' : '') + departure.getMinutes()} Uhr`
        });
    } catch (e) {
        res.status(404).send({
            "error": "no route found"
        })
    }
});

module.exports = router;