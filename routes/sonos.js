const express = require('express');
const router = express.Router();
const axios = require("axios");
const fs = require('fs');

let expiresAt;
let accessToken;

let refreshToken = getRefreshToken();

function getRefreshToken() {
    try {
        return fs.readFileSync('.sonos_refresh_token').toString();
    } catch (e) {
        return null;
    }
}

function setRefreshToken(token) {
    refreshToken = token;
    fs.writeFileSync(".sonos_refresh_token", token);
}

router.get('/', async (req, res) => {
    if (!process.env.MODULE_SONOS_CLIENT_ID) {
        return;
    }
    const getToken = async () => {
        if (expiresAt && Date.now() < expiresAt) {
            return accessToken;
        }

        const auth = Buffer.from(process.env.MODULE_SONOS_CLIENT_ID + ':' + process.env.MODULE_SONOS_CLIENT_SECRET, 'utf-8').toString('base64');
        
        const options = {
            method: 'POST',
            url: 'https://api.sonos.com/login/v3/oauth/access',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                Authorization: `Basic ${auth}`
            },
            data: `grant_type=refresh_token&refresh_token=${refreshToken}`
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

    const service = metadata.container.service ? metadata.container.service.name.toLowerCase() : metadata.container.type.toLowerCase();

    if (service == 'linein.hometheater') {
        res.send({
            name: 'Fernseher',
            detail: null,
            image: null
        })
    } else if (service == "tunein") {
        res.send({
            name: metadata.container.name,
            detail: metadata.streamInfo ? metadata.streamInfo : null,
            image: metadata.container.imageUrl ? metadata.container.imageUrl : `https://cdn-profiles.tunein.com/${metadata.container.id.objectId}/images/logoq.jpg`
        });
    } else if (service.split(':')[0] == 'spotify' || service == 'playlist.spotify.connect' || service == 'linein.airplay') {
        res.send({
            name: metadata.currentItem.track.artist.name,
            detail: metadata.currentItem.track.name,
            image: metadata.currentItem.track.imageUrl
        });
    }
});

module.exports = router;
