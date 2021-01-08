const express = require('express');
const router = express.Router();
const icloud = require('icloud-shared-album');

router.get('/', async (req, res) => {
    const data = await icloud.getImages(process.env.MODULE_ICLOUD_ALBUM);
    res.send({
        images: data.map(image => image.url)
    });
});

module.exports = router;