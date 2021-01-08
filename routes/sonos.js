const express = require('express');
const router = express.Router();
const axios = require("axios");
const FormData = require('form-data');
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

        const formData = new FormData();

        formData.append('grant_type', 'refresh_token');
        formData.append('refresh_token', refreshToken);

        const auth = Buffer.from(process.env.MODULE_SONOS_CLIENT_ID + ':' + process.env.MODULE_SONOS_CLIENT_SECRET, 'utf-8').toString('base64');
        const headers = { ...formData.getHeaders(), Authorization: `Basic ${auth}` };

        const responseToken = await axios.post('https://api.sonos.com/login/v3/oauth/access', formData, {
            headers
        });
       
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