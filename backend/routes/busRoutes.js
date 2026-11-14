const express = require('express');
const router = express.Router();
const busController = require('../controllers/busController');

// Search buses
router.get('/search', busController.searchBuses);

// Get available cities
router.get('/cities', busController.getAllCities);

// Get schedule seats layout
router.get('/schedules/:scheduleId/seats', busController.getScheduleSeats);

// Get bus details by id
router.get('/:id', busController.getBusDetails);

module.exports = router;
