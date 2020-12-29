/*
MODULE_TESLA_CLIENT_ID
MODULE_TESLA_CLIENT_SECRET
MODULE_TESLA_EMAIL
MODULE_TESLA_PASSWORD

MODULE_NETATMO_CLIENT_ID
MODULE_NETATMO_CLIENT_SECRET
MODULE_NETATMO_USERNAME
MODULE_NETATMO_PASSWORD
MODULE_NETATMO_DEVICE_ID

MODULE_EOGUIDE_CLIENT_KEY
MODULE_EOGUIDE_USERNAME
MODULE_EOGUIDE_PASSWORD
*/

'use strict';

require('dotenv').config()
const express = require('express');

const publicTransportation = require('./routes/public-transportation');
const eoGuide = require('./routes/eo-guide');
const netatmo = require('./routes/netatmo');
const tesla = require('./routes/tesla');

const PORT = process.env.PORT || 3000;
const HOST = '0.0.0.0';

const app = express();
app.get('/', (req, res) => {
  res.send('DAKBoard API');
});

app.use('/public-transportation', publicTransportation);
app.use('/eo-guide', eoGuide);
app.use('/netatmo', netatmo);
app.use('/tesla', tesla);

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);
