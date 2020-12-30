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

    const responseReview = await axios.get(`https://api.appfigures.com/v2/reviews/?count=1&client_key=${process.env.MODULE_EOGUIDE_CLIENT_KEY}`, {
        auth: {
            username: process.env.MODULE_EOGUIDE_USERNAME,
            password: process.env.MODULE_EOGUIDE_PASSWORD
        }
    });

    res.send({
        total: response.data.downloads,
        totalFormatted: response.data.downloads.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "'"),
        latestReview: {
            review: responseReview.data.reviews[0].review,
            reviewFormatted: responseReview.data.reviews[0].review.replace(/([\uE000-\uF8FF]|\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDDFF])/g, '').trim(),
            stars: responseReview.data.reviews[0].stars,
            starsFormatted: Math.round(responseReview.data.reviews[0].stars * 10) / 10
        }
    });
});

module.exports = router;