const express = require('express');
const router = express.Router();
const bookingController = require('../controllers/bookingController');
const { generateTicketPDF } = require('../services/ticketService');
const { verifyToken } = require('../middleware/authMiddleware');
const { pool } = require('../config/db');

// Protected routes
router.post('/lock-seats', verifyToken, bookingController.lockSeats);
router.post('/validate-coupon', verifyToken, bookingController.validateCoupon);
router.post('/create', verifyToken, bookingController.createBooking);
router.get('/my-bookings', verifyToken, bookingController.getMyBookings);
router.get('/:id', verifyToken, bookingController.getBookingById);
router.post('/cancel/:id', verifyToken, bookingController.cancelBooking);

// Ticket PDF Download endpoint
router.get('/:id/download-ticket', verifyToken, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.userId;

    const [bookings] = await pool.query(
      `SELECT bk.*, 
              s.schedule_id, s.journey_date, s.departure_time, s.arrival_time,
              b.bus_name, b.bus_number, b.bus_type,
              r.source_city, r.destination_city,
              o.company_name as operator_name,
              bs1.stop_name as boarding_point,
              bs2.stop_name as dropping_point,
              u.name as user_name
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       JOIN operators o ON b.operator_id = o.operator_id
       JOIN users u ON bk.user_id = u.user_id
       LEFT JOIN bus_stops bs1 ON bk.boarding_stop_id = bs1.stop_id
       LEFT JOIN bus_stops bs2 ON bk.dropping_stop_id = bs2.stop_id
       WHERE bk.booking_id = ? AND (bk.user_id = ? OR ? = 'admin')`,
      [id, userId, req.user.role]
    );

    if (bookings.length === 0) {
      return res.status(404).json({ success: false, message: 'Booking not found.' });
    }

    const booking = bookings[0];

    const [passengers] = await pool.query(
      'SELECT passenger_name, age, gender, seat_number FROM passengers WHERE booking_id = ?',
      [id]
    );
    booking.passengers = passengers;

    const pdfBuffer = await generateTicketPDF(booking);

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=BUSGO_Ticket_${booking.pnr_number}.pdf`);
    res.setHeader('Content-Length', pdfBuffer.length);
    return res.end(pdfBuffer);
  } catch (error) {
    console.error('[BookingRoutes] download-ticket error:', error);
    return res.status(500).json({ success: false, message: 'Failed to generate ticket PDF.' });
  }
});

module.exports = router;
