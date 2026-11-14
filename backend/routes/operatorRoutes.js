const express = require('express');
const router = express.Router();
const operatorController = require('../controllers/operatorController');
const { verifyToken } = require('../middleware/authMiddleware');
const { requireRole } = require('../middleware/roleMiddleware');

// All operator routes require verifyToken and 'operator' or 'admin' role
router.use(verifyToken, requireRole('operator', 'admin'));

router.get('/dashboard', operatorController.getDashboard);
router.get('/buses', operatorController.getMyBuses);
router.post('/buses', operatorController.addBus);
router.post('/schedules', operatorController.addSchedule);
router.post('/routes', operatorController.addRoute);
router.get('/routes', operatorController.getAllRoutes);
router.get('/bookings', operatorController.getMyBookings);

module.exports = router;
