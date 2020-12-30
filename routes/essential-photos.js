const express = require('express');
const router = express.Router();
const axios = require('axios').default;

router.get('/', async (req, res) => {
    const responseIG = await axios.get('https://www.instagram.com/essentialphotoscom/?__a=1');
    const IGCount = responseIG.data.graphql.user.edge_followed_by.count;

    const responseFB = await axios.get('http://www.facebook.com/plugins/fan.php?connections=100&id=essentialphotoscom');
    const result = responseFB.data.match(/([0-9]*) „Gefällt mir“/);
    const FBCount = parseInt(result[1]);

    res.send({
        facebook: FBCount,
        instagram: IGCount
    })
});

module.exports = router;