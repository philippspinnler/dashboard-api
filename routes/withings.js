const express = require('express');
const router = express.Router();
const axios = require("axios");
const FormData = require('form-data');
const fs = require('fs');

let expiresAt = {};
let accessToken = {}

let refreshTokens = getRefreshTokens();

function getRefreshTokens() {
    try {
        return JSON.parse(fs.readFileSync('.withings_refresh_tokens'));
    } catch(e) {
        return [];
    }
}

function setRefreshToken(person, token) {
    const refreshToken = refreshTokens.find(refreshTokenTmp => refreshTokenTmp.person == person);
    refreshToken.token = token === undefined ? null : token;
    fs.writeFileSync(".withings_refresh_tokens", JSON.stringify(refreshTokens));
}

function onlyShowOneDecimal(num) {
    num = num.toString();
    num = num.slice(0, (num.indexOf(".")) + 2);
    return Number(num);
}

router.get('/', async (req, res) => {
    const finalResponse = {};

    for (const refreshToken of refreshTokens) {
        const getToken = async () => {
            if (expiresAt[refreshToken.person] && Date.now() < expiresAt[refreshToken.person]) {
                return accessToken[refreshToken.person];
            }

            const formData = new FormData();

            formData.append('action', 'requesttoken');
            formData.append('client_id', process.env.MODULE_WITHINGS_CLIENT_ID);
            formData.append('client_secret', process.env.MODULE_WITHINGS_CLIENT_SECRET);
            formData.append('grant_type', 'refresh_token');
            formData.append('refresh_token', refreshToken.token ? refreshToken.token : '');

            const responseToken = await axios.post('https://wbsapi.withings.net/v2/oauth2', formData, {
                headers: formData.getHeaders()
            });
            expiresAt[refreshToken.person] = ((Date.now() / 1000) + responseToken.data.body.expires_in) * 1000;
            
            setRefreshToken(refreshToken.person, responseToken.data.body.refresh_token);

            return responseToken.data.body.access_token;
        }

        accessToken[refreshToken.person] = await getToken();

        const response = await axios.get(`https://wbsapi.withings.net/measure?action=getmeas`, {
            headers: {
                Authorization: `Bearer ${accessToken[refreshToken.person]}`
            }
        });

        const currentWeight = response.data.body.measuregrps[0].measures[0].value;
        const lastWeight = response.data.body.measuregrps[1].measures[0].value;

        const currentWeightFormatted = `${onlyShowOneDecimal((currentWeight / 1000))} kg`;

        let deltaWithOneDecimal = onlyShowOneDecimal(((currentWeight - lastWeight) / 1000));
        if (deltaWithOneDecimal > 0) {
            deltaWithOneDecimal = `+${deltaWithOneDecimal}`;
        }
        const deltaSinceLastMeasureFormatted = `${deltaWithOneDecimal} kg`;

        finalResponse[refreshToken.person] = {
            currentWeight,
            currentWeightFormatted,
            deltaSinceLastMeasureFormatted
        };
    }

    res.send(finalResponse);
});

module.exports = router;

// https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=[CLIENT_ID]&state=blubb&scope=user.metrics&redirect_uri=https://dashboard.monphi.ch/withings/callback