const express = require('express');
const router = express.Router();
const axios = require('axios').default;
const FormData = require('form-data');

let expiresAt = null;
let refreshToken = null;
let accessToken = null;

router.get('/', async (req, res) => {
    const getToken = async () => {
        if (expiresAt && Date.now() < expiresAt) {
            return accessToken;
        }

        const formData = new FormData();

        if (expiresAt && Date.now() >= expiresAt) {
            formData.append('grant_type', 'refresh_token');
            formData.append('client_id', process.env.MODULE_NETATMO_CLIENT_ID);
            formData.append('client_secret', process.env.MODULE_NETATMO_CLIENT_SECRET);
            formData.append('refresh_token', refreshToken);
        } else {
            formData.append('grant_type', 'password');
            formData.append('client_id', process.env.MODULE_NETATMO_CLIENT_ID);
            formData.append('client_secret', process.env.MODULE_NETATMO_CLIENT_SECRET);
            formData.append('username', process.env.MODULE_NETATMO_USERNAME);
            formData.append('password', process.env.MODULE_NETATMO_PASSWORD);
            formData.append('scope', 'read_station read_thermostat');
        }

        const responseToken = await axios.post('https://api.netatmo.com/oauth2/token', formData, {
            headers: formData.getHeaders()
        });
        expiresAt = ((Date.now() / 1000) + responseToken.data.expires_in) * 1000;
        refreshToken = responseToken.data.refresh_token;
        return responseToken.data.access_token;
    }

    accessToken = await getToken();

    const response = await axios.get(`https://api.netatmo.com/api/getstationsdata?device_id=${process.env.MODULE_NETATMO_DEVICE_ID}`, {
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    });

    const temperature = response.data.body.devices[0].dashboard_data.Temperature;
    const co2 = response.data.body.devices[0].dashboard_data.CO2;
    
    res.send({
        temperature,
        temperatureFormatted: `${temperature} °C`,
        co2,
        co2Formatted: `${co2} ppm`,
        modules: response.data.body.devices[0].modules.filter(module => module.data_type.includes('Temperature') && module.hasOwnProperty('dashboard_data')).map(module => {
            return {
                module_name: module.module_name,
                temperature: module.dashboard_data.Temperature,
                temperatureFormatted: `${module.dashboard_data.Temperature} °C`,
                batteryPercent: module.battery_percent
            }
        })
    })
});

module.exports = router;