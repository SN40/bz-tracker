// Datei: project/api/v1/users.js
const express = require('express');
const router = express.Router();

// GET-Anfrage an /api/v1/users
router.get('/', (req, res) => {
    res.json({
        version: "v1",
        users: [
            { id: 1, name: "Max Mustermann" }
        ]
    });
});

module.exports = router;
