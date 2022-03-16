const express = require('express');
const router = express.Router();
const axiosRaw = require('axios').default;
const dayjs = require('dayjs');
const https = require('https');


router.get('/', async (req, res) => {
    const axios = axiosRaw.create({
        httpsAgent: new https.Agent({  
            rejectUnauthorized: false
        }),
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
    });

    const agent = new https.Agent({  
        rejectUnauthorized: false
    });
    const response_login = await axios.post(`https://${process.env.UNIFI_HOST}/api/auth/login`, {
        username: process.env.UNIFI_USERNAME,
        password: process.env.UNIFI_PASSWORD
        },
        { httpsAgent: agent });
    cookie = response_login.headers['set-cookie'][0];

    const response_health = await axios.get(`https://${process.env.UNIFI_HOST}/proxy/network/api/s/default/stat/health`, {
        headers:{
            Cookie: cookie
        } 
    });

    const wan = response_health.data.data.find(subsystem => subsystem.subsystem == "www");

    getReadableFileSizeString = fileSizeInBytes => {

        var i = -1;
        var byteUnits = [' Kbps', ' Mbps', ' Gbps', ' Tbps'];
        do {
            fileSizeInBytes = fileSizeInBytes / 1024;
            i++;
        } while (fileSizeInBytes > 1024);
    
        return Math.max(fileSizeInBytes, 0.1).toFixed(1) + byteUnits[i];
        };

    res.send({
        "latency": wan.latency,
        "currentUpBytes": wan["tx_bytes-r"],
        "currentDownBytes": wan["rx_bytes-r"],
        "currentUpFormatted": getReadableFileSizeString(wan["tx_bytes-r"]*8),
        "currentDownFormatted": getReadableFileSizeString(wan["rx_bytes-r"]*8)
    });
});

module.exports = router;