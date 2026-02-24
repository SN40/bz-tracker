// Datei: project/app.js
const express = require('express');
const app = express();

// Wir binden den V1-Ordner ein
const v1Api = require('./api/v1/index');

// Alles was mit /api/v1 beginnt, geht in den V1-Ordner
app.use('/api/v1', v1Api);

app.listen(3000, () => console.log("API läuft auf Port 3000"));
