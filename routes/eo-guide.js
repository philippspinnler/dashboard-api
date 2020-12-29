const express = require('express');
const router = express.Router();
const axios = require('axios').default;

router.get('/', async (req, res) => {
    const response = await axios.get(`https://api.appfigures.com/v2/reports/sales/?client_key=${process.env.MODULE_EOGUIDE_CLIENT_KEY}`, {
        auth: {
            username: process.env.MODULE_EOGUIDE_USERNAME,
            password: process.env.MODULE_EOGUIDE_PASSWORD
        }
    });

    res.send({
        total: response.data.downloads,
        totalFormatted: response.data.downloads.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "'")
    });
});

router.get('/reviews/latest', async (req, res) => {
    const response = await axios.get(`https://api.appfigures.com/v2/reviews/?count=1&client_key=${process.env.MODULE_EOGUIDE_CLIENT_KEY}`, {
        auth: {
            username: process.env.MODULE_EOGUIDE_USERNAME,
            password: process.env.MODULE_EOGUIDE_PASSWORD
        }
    });

    res.send({
        review: response.data.reviews[0].review,
        reviewFormatted: response.data.reviews[0].review.replace(/([\uE000-\uF8FF]|\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDDFF])/g, '').trim(),
        stars: response.data.reviews[0].stars,
        starsFormatted: Math.round(response.data.reviews[0].stars * 10) / 10
    });
});

module.exports = router;