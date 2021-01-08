const express = require('express');
const router = express.Router();
const axios = require('axios').default;
const dayjs = require('dayjs');


router.get('/', async (req, res) => {
    
    const lat = 47.4176969;
    const lon = 7.7612123;
    const units = 'metric';
    const lang = 'de';
    const exclude = 'minutely,hourly,alerts';
    const appId = process.env.MODULE_WEATHER_API_KEY;
    const response = await axios.get(`https://api.openweathermap.org/data/2.5/onecall?lat=${lat}&lon=${lon}&units=${units}&lang=${lang}&exclude=${exclude}&appid=${appId}`);
    
    res.send({
        current: {
            temperature: response.data.current.temp,
            temperatureFeelsLike: response.data.current.feels_like,
            weather: response.data.current.weather.map(weather => {
                return {
                    id: weather.id,
                    icon: weather.icon,
                    description: weather.description
                }
            })
        },
        daily: response.data.daily.map(day => {
            return {
                date: dayjs.unix(day.dt),
                temperature: {
                    min: day.temp.min,
                    max: day.temp.max
                },
                weather: day.weather.map(weather => {
                    return {
                        id: weather.id,
                        icon: weather.icon,
                        description: weather.description
                    }
                })
            }
        })
    })
});

module.exports = router;