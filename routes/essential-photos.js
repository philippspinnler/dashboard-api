const express = require('express');
const router = express.Router();
const axios = require('axios').default;
const Instagram = require('instagram-web-api')

router.get('/', async (req, res) => {
    try {
        const client = new Instagram({ username: process.env.MODULE_ESSENTIAL_PHOTOS_USERNAME, password: process.env.MODULE_ESSENTIAL_PHOTOS_PASSWORD })
        await client.login()
        const followers = await client.getFollowers({ userId: process.env.MODULE_ESSENTIAL_PHOTOS_FOLLOWERS_USER_ID })

        const responseFB = await axios.get('http://www.facebook.com/plugins/fan.php?connections=100&id=essentialphotoscom');
        const result = responseFB.data.match(/([0-9]*) „Gefällt mir“/);
        const FBCount = parseInt(result[1]);
        res.send({
            facebook: FBCount,
            instagram: followers.count
        })
    } catch(e) {
        console.log(e);
    }
    
});

module.exports = router;