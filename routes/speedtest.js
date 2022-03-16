const express = require('express');
const router = express.Router();
const axios = require('axios').default;
const dayjs = require('dayjs');
const https = require('https');


router.get('/', async (req, res) => {
    const response = await axios.get(`http://10.0.86.11:8765/api/speedtest/home/7`);

    getReadableFileSizeString = fileSizeInBytes => {

        var i = -1;
        var byteUnits = [' Kbps', ' Mbps', ' Gbps', ' Gbps'];
        do {
            fileSizeInBytes = fileSizeInBytes / 1024;
            i++;
        } while (fileSizeInBytes > 1024);
    
        return Math.max(fileSizeInBytes, 0.1).toFixed(1) + byteUnits[i];
        };

    res.send({
        download: response.data.latest.data.download,
        upload: response.data.latest.data.upload,
        downloadFormatted: getReadableFileSizeString(response.data.latest.data.download*1024*1024),
        uploadFormatted: getReadableFileSizeString(response.data.latest.data.upload*1024*1024),
        ping: response.data.latest.data.ping
    });
});

module.exports = router;