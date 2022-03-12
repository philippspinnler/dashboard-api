'use strict';

require('dotenv').config()
const express = require('express');
const cors = require('cors')
const timeout = require('connect-timeout')
const apicache = require('apicache');
const cache = apicache.middleware

const auth = require('./middleware/auth');

const publicTransportation = require('./routes/public-transportation');
const eoGuide = require('./routes/eo-guide');
const netatmo = require('./routes/netatmo');
const tesla = require('./routes/tesla');
const essentialPhotos = require('./routes/essential-photos');
const withings = require('./routes/withings');
const icloudAlbum = require('./routes/icloud-album');
const ical = require('./routes/ical');
const weather = require('./routes/weather');
const sonos = require('./routes/sonos');
const simpleQuote = require('./routes/simple-quote');
const unifi = require('./routes/unifi');

const PORT = process.env.PORT || 3000;
const HOST = '0.0.0.0';

const app = express();
app.use(cors());
app.use(timeout('30s'))

app.get('/', (req, res) => {
  res.send('DAKBoard API');
});

app.use('/public-transportation', auth, publicTransportation);
app.use('/eo-guide', auth, cache('4 hours'), eoGuide);
app.use('/netatmo', auth, cache('1 minutes'), netatmo);
app.use('/tesla', auth, tesla);
app.use('/essential-photos', cache('4 hours'), auth, essentialPhotos);
app.use('/withings', cache('10 minutes'), auth, withings);
app.use('/icloud-album', cache('1 hours'), auth, icloudAlbum);
app.use('/ical', cache('5 minutes'), auth, ical);
app.use('/weather', cache('1 hours'), auth, weather);
app.use('/sonos', cache('5 seconds'), auth, sonos);
app.use('/simple-quote', cache('5 seconds'), auth, simpleQuote);
app.use('/unifi', cache('5 seconds'), auth, unifi);

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);
