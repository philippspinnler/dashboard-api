const express = require('express');
const router = express.Router();
const axios = require('axios').default;
const dayjs = require('dayjs');

let lastUpdated = null;
let cachedResponse = null;

router.get('/', async (req, res) => {

    if (!lastUpdated || !dayjs().isSame(lastUpdated, 'day')) {
        const options = {
            method: 'GET',
            url: 'https://simplequote.spinnler.ch/api/simplequote.php',
            auth: {
                username: process.env.MODULE_SIMPLE_QUOTE_USERNAME,
                password: process.env.MODULE_SIMPLE_QUOTE_PASSWORD
            }
        };
    
        const response = await axios.request(options);
    
        cachedResponse = response.data;

        lastUpdated = dayjs()
    }
     
    res.send(cachedResponse);
});

module.exports = router;