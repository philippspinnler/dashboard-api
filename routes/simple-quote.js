const express = require('express');
const router = express.Router();
const axios = require('axios').default;

router.get('/', async (req, res) => {

    const options = {
        method: 'GET',
        url: 'https://simplequote.spinnler.ch/api/simplequote.php',
        auth: {
            username: process.env.MODULE_SIMPLE_QUOTE_USERNAME,
            password: process.env.MODULE_SIMPLE_QUOTE_PASSWORD
        }
    };

    const response = await axios.request(options);

    const parsed = response.data;
    
    res.send(parsed);
});

module.exports = router;