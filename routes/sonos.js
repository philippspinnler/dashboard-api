const express = require('express');
const router = express.Router();
const axios = require("axios");
const fs = require('fs');

let expiresAt;
let accessToken;

let refreshToken = getRefreshToken();

function getRefreshToken() {
    try {
        return fs.readFileSync('.sonos_refresh_token');
    } catch (e) {
        return null;
    }
}

function setRefreshToken(token) {
    refreshToken = token;
    fs.writeFileSync(".sonos_refresh_token", token);
}

router.get('/', async (req, res) => {
    const getToken = async () => {
        if (expiresAt && Date.now() < expiresAt) {
            return accessToken;
        }

        const auth = Buffer.from(process.env.MODULE_SONOS_CLIENT_ID + ':' + process.env.MODULE_SONOS_CLIENT_SECRET, 'utf-8').toString('base64');
        
        const options = {
            method: 'POST',
            url: 'https://api.sonos.com/login/v3/oauth/access',
            headers: {
                'Content-Type': 'multipart/form-data',
                Authorization: `Basic ${auth}`,
                'content-type': 'multipart/form-data; boundary=---011000010111000001101001'
            },
            data: `-----011000010111000001101001\r\nContent-Disposition: form-data; name="grant_type"\r\n\r\nrefresh_token\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name="refresh_token"\r\n\r\n${refreshToken}\r\n-----011000010111000001101001--\r\n`
        };

        const responseToken = await axios.request(options);
       
        expiresAt = ((Date.now() / 1000) + responseToken.data.expires_in) * 1000;

        setRefreshToken(responseToken.data.refresh_token);

        return responseToken.data.access_token;
    }

    accessToken = await getToken();

    const responseHouseholds = await axios.get("https://api.ws.sonos.com/control/api/v1/households", {
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    });

    const householdId = responseHouseholds.data.households[0].id;

    const responseGroups = await axios.get(`https://api.ws.sonos.com/control/api/v1/households/${householdId}/groups`, {
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    });

    const group = responseGroups.data.groups.find(g => g.playbackState == "PLAYBACK_STATE_PLAYING");

    if (!group) {
        res.status(204).send();
        return;
    }

    const responseMetadata = await axios.get(`https://api.ws.sonos.com/control/api/v1/groups/${group.id}/playbackMetadata`, {
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    });
    
    const metadata = responseMetadata.data;

    if (metadata.container.type == 'linein.homeTheater') {
        res.send({
            name: 'Fernseher',
            detail: null,
            image: null
        })
        return;
    }

    const service = metadata.container.service.name;

    if (service.toLowerCase() == "tunein") {
        res.send({
            name: metadata.container.name,
            detail: null,
            image: metadata.container.imageUrl ? metadata.container.imageUrl : `https://cdn-profiles.tunein.com/${metadata.container.id.objectId}/images/logoq.jpg`
        });
    } else if (service.toLowerCase().split(':')[0] == 'spotify') {
        res.send({
            name: metadata.currentItem.track.artist.name,
            detail: metadata.currentItem.track.name,
            image: metadata.currentItem.track.imageUrl
        });
    }
});

module.exports = router;