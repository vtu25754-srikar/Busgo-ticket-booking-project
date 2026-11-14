const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');
const { verifyToken } = require('../middleware/authMiddleware');
const { requireRole } = require('../middleware/roleMiddleware');

// All admin routes require verifyToken and 'admin' role
router.use(verifyToken, requireRole('admin'));

router.get('/dashboard', adminController.getDashboardStats);
router.get('/users', adminController.getAllUsers);
router.put('/users/:id/status', adminController.updateUserStatus);
router.get('/operators', adminController.getAllOperators);
router.put('/operators/:id/status', adminController.updateOperatorStatus);
router.get('/bookings', adminController.getAllBookings);
router.get('/buses', adminController.getAllBuses);

module.exports = router;
