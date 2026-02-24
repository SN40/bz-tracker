// Datei: project/api/v1/index.js
const express = require('express');
const router = express.Router();

// Hier binden wir die spezifischen Ressourcen für V1 ein
const userRoutes = require('./users');

router.use('/users', userRoutes);

module.exports = router;


