const { pool } = require('../config/db');
const { generatePNR, generateTransactionId } = require('../utils/generatePNR');
const { calculateRefund, releaseExpiredLocks } = require('../services/bookingService');
const { sendBookingConfirmation, sendCancellationEmail } = require('../utils/emailService');

/**
 * Temporarily lock seats during checkout (prevents double booking)
 * Locks seats for 10 minutes for this user
 */
async function lockSeats(req, res) {
  const connection = await pool.getConnection();
  try {
    const { scheduleId, seatIds } = req.body;
    const userId = req.user.userId;

    if (!scheduleId || !Array.isArray(seatIds) || seatIds.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Schedule ID and at least one seat ID are required.'
      });
    }

    await connection.beginTransaction();

    // Release any expired locks first
    await connection.query(
      `UPDATE seat_availability 
       SET status = 'available', locked_until = NULL, locked_by = NULL 
       WHERE schedule_id = ? AND status = 'locked' AND locked_until < NOW()`,
      [scheduleId]
    );

    // Check availability of requested seats
    const [existingSeats] = await connection.query(
      `SELECT sa.seat_id, sa.status, sa.locked_by, sa.locked_until, s.seat_number 
       FROM seats s
       LEFT JOIN seat_availability sa ON s.seat_id = sa.seat_id AND sa.schedule_id = ?
       WHERE s.seat_id IN (?) FOR UPDATE`,
      [scheduleId, seatIds]
    );

    for (const seat of existingSeats) {
      // If seat is already booked
      if (seat.status === 'booked') {
        await connection.rollback();
        return res.status(409).json({
          success: false,
          message: `Seat ${seat.seat_number} is already booked by another customer.`
        });
      }

      // If seat is currently locked by someone else
      if (seat.status === 'locked' && seat.locked_by !== userId) {
        await connection.rollback();
        return res.status(409).json({
          success: false,
          message: `Seat ${seat.seat_number} is currently reserved by another customer. Please choose a different seat.`
        });
      }
    }

    // Lock seats for 10 minutes
    const lockedUntil = new Date(Date.now() + 10 * 60 * 1000);

    for (const seatId of seatIds) {
      await connection.query(
        `INSERT INTO seat_availability (seat_id, schedule_id, status, locked_until, locked_by)
         VALUES (?, ?, 'locked', ?, ?)
         ON DUPLICATE KEY UPDATE status = 'locked', locked_until = VALUES(locked_until), locked_by = VALUES(locked_by)`,
        [seatId, scheduleId, lockedUntil, userId]
      );
    }

    await connection.commit();

    return res.json({
      success: true,
      message: 'Seats reserved for 10 minutes.',
      lockedUntil,
      lockedSeats: seatIds
    });
  } catch (error) {
    await connection.rollback();
    console.error('[BookingController] lockSeats error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to reserve seats. Please try again.'
    });
  } finally {
    connection.release();
  }
}

/**
 * Validate and apply coupon code
 */
async function validateCoupon(req, res) {
  try {
    const { code, amount } = req.body;

    if (!code) {
      return res.status(400).json({ success: false, message: 'Coupon code is required.' });
    }

    const [coupons] = await pool.query(
      `SELECT * FROM coupons 
       WHERE code = ? AND is_active = 1 
         AND (valid_from IS NULL OR valid_from <= CURDATE())
         AND (valid_until IS NULL OR valid_until >= CURDATE())
       LIMIT 1`,
      [code.trim().toUpperCase()]
    );

    if (coupons.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Invalid or expired coupon code.'
      });
    }

    const coupon = coupons[0];
    const bookingAmount = Number(amount || 0);

    if (bookingAmount < Number(coupon.min_booking_amount)) {
      return res.status(400).json({
        success: false,
        message: `This coupon requires a minimum booking amount of ₹${coupon.min_booking_amount}.`
      });
    }

    let discount = 0;
    if (coupon.discount_type === 'percentage') {
      discount = (bookingAmount * Number(coupon.discount_value)) / 100;
      if (coupon.max_discount && discount > Number(coupon.max_discount)) {
        discount = Number(coupon.max_discount);
      }
    } else {
      discount = Number(coupon.discount_value);
    }

    discount = Math.min(discount, bookingAmount);

    return res.json({
      success: true,
      message: 'Coupon applied successfully!',
      couponCode: coupon.code,
      discountAmount: Math.round(discount * 100) / 100
    });
  } catch (error) {
    console.error('[BookingController] validateCoupon error:', error);
    return res.status(500).json({ success: false, message: 'Failed to validate coupon.' });
  }
}

/**
 * Create a new booking
 */
async function createBooking(req, res) {
  const connection = await pool.getConnection();
  try {
    const {
      scheduleId,
      passengers, // Array of { name, age, gender, seatId, seatNumber }
      boardingStopId,
      droppingStopId,
      couponCode
    } = req.body;

    const userId = req.user.userId;

    if (!scheduleId || !Array.isArray(passengers) || passengers.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Schedule and passenger details are required.'
      });
    }

    await connection.beginTransaction();

    // 1. Fetch Schedule Details
    const [schedules] = await connection.query(
      `SELECT s.*, b.bus_id, b.bus_name, b.bus_type, r.source_city, r.destination_city
       FROM schedules s
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       WHERE s.schedule_id = ? FOR UPDATE`,
      [scheduleId]
    );

    if (schedules.length === 0) {
      await connection.rollback();
      return res.status(404).json({ success: false, message: 'Schedule not found.' });
    }

    const schedule = schedules[0];
    const seatIds = passengers.map(p => p.seatId);

    // 2. Re-verify seats are available or locked by this user
    const [availCheck] = await connection.query(
      `SELECT seat_id, status, locked_by 
       FROM seat_availability 
       WHERE schedule_id = ? AND seat_id IN (?) FOR UPDATE`,
      [scheduleId, seatIds]
    );

    for (const record of availCheck) {
      if (record.status === 'booked') {
        await connection.rollback();
        return res.status(409).json({
          success: false,
          message: 'One or more of the selected seats were already booked. Please reselect.'
        });
      }
      if (record.status === 'locked' && record.locked_by !== userId) {
        await connection.rollback();
        return res.status(409).json({
          success: false,
          message: 'Seats are locked by another user. Please choose different seats.'
        });
      }
    }

    // 3. Calculate Fare
    const ticketPrice = Number(schedule.ticket_price);
    const seatCount = passengers.length;
    const baseAmount = ticketPrice * seatCount;
    const convenienceFee = 50.00;
    const taxes = Math.round(baseAmount * 0.05 * 100) / 100; // 5% GST

    let discountAmount = 0;
    if (couponCode) {
      const [coupons] = await connection.query(
        `SELECT * FROM coupons WHERE code = ? AND is_active = 1 LIMIT 1`,
        [couponCode.trim().toUpperCase()]
      );
      if (coupons.length > 0) {
        const c = coupons[0];
        if (c.discount_type === 'percentage') {
          discountAmount = (baseAmount * Number(c.discount_value)) / 100;
          if (c.max_discount && discountAmount > Number(c.max_discount)) {
            discountAmount = Number(c.max_discount);
          }
        } else {
          discountAmount = Number(c.discount_value);
        }
      }
    }

    const totalAmount = Math.max(0, baseAmount + convenienceFee + taxes - discountAmount);

    // 4. Generate PNR
    const pnr = generatePNR();

    // 5. Insert Booking Record
    const [bookingResult] = await connection.query(
      `INSERT INTO bookings 
        (user_id, schedule_id, total_amount, convenience_fee, taxes, discount_amount, 
         booking_status, pnr_number, boarding_stop_id, dropping_stop_id, coupon_code)
       VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?, ?)`,
      [userId, scheduleId, totalAmount, convenienceFee, taxes, discountAmount,
       pnr, boardingStopId || null, droppingStopId || null, couponCode || null]
    );

    const bookingId = bookingResult.insertId;

    // 6. Insert Passengers and mark seats as booked
    for (const p of passengers) {
      await connection.query(
        `INSERT INTO passengers (booking_id, passenger_name, age, gender, seat_id, seat_number)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [bookingId, p.name.trim(), parseInt(p.age, 10), p.gender.toLowerCase(), p.seatId, p.seatNumber]
      );

      await connection.query(
        `INSERT INTO seat_availability (seat_id, schedule_id, status, locked_until, locked_by)
         VALUES (?, ?, 'booked', NULL, NULL)
         ON DUPLICATE KEY UPDATE status = 'booked', locked_until = NULL, locked_by = NULL`,
        [p.seatId, scheduleId]
      );
    }

    // 7. Update available seats on schedule
    await connection.query(
      `UPDATE schedules SET available_seats = GREATEST(0, available_seats - ?) WHERE schedule_id = ?`,
      [seatCount, scheduleId]
    );

    // 8. Create Payment Record (pre-confirmed for testing or linked to razorpay)
    const txnId = generateTransactionId();
    await connection.query(
      `INSERT INTO payments 
        (booking_id, transaction_id, amount, payment_method, payment_status, payment_date)
       VALUES (?, ?, ?, 'UPI / Online', 'success', NOW())`,
      [bookingId, txnId, totalAmount]
    );

    await connection.commit();

    // Send confirmation email asynchronously
    const seatNumbers = passengers.map(p => p.seatNumber);
    sendBookingConfirmation(req.user.email, {
      pnr,
      busName: schedule.bus_name,
      journeyDate: schedule.journey_date,
      departureTime: schedule.departure_time,
      fromCity: schedule.source_city,
      toCity: schedule.destination_city,
      seats: seatNumbers,
      totalAmount,
      passengerCount: seatCount
    }).catch(err => console.error('[BookingController] Email error:', err.message));

    return res.status(201).json({
      success: true,
      message: 'Bus ticket booked successfully!',
      booking: {
        bookingId,
        pnr,
        totalAmount,
        seats: seatNumbers,
        status: 'confirmed',
        journeyDate: schedule.journey_date,
        departureTime: schedule.departure_time,
        sourceCity: schedule.source_city,
        destinationCity: schedule.destination_city,
        busName: schedule.bus_name
      }
    });
  } catch (error) {
    await connection.rollback();
    console.error('[BookingController] createBooking error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to create booking.'
    });
  } finally {
    connection.release();
  }
}

/**
 * Get all bookings for the logged-in user
 */
async function getMyBookings(req, res) {
  try {
    const userId = req.user.userId;

    const [bookings] = await pool.query(
      `SELECT bk.booking_id, bk.pnr_number, bk.booking_date, bk.total_amount, 
              bk.booking_status, bk.created_at,
              s.schedule_id, s.journey_date, s.departure_time, s.arrival_time,
              b.bus_name, b.bus_number, b.bus_type,
              r.source_city, r.destination_city,
              o.company_name as operator_name,
              p.payment_status, p.payment_method, p.transaction_id,
              GROUP_CONCAT(DISTINCT ps.seat_number ORDER BY ps.seat_number SEPARATOR ', ') as seats_booked,
              COUNT(DISTINCT ps.passenger_id) as passenger_count
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       JOIN operators o ON b.operator_id = o.operator_id
       LEFT JOIN payments p ON bk.booking_id = p.booking_id
       LEFT JOIN passengers ps ON bk.booking_id = ps.booking_id
       WHERE bk.user_id = ?
       GROUP BY bk.booking_id
       ORDER BY bk.created_at DESC`,
      [userId]
    );

    const today = new Date().toISOString().split('T')[0];

    const upcoming = [];
    const completed = [];
    const cancelled = [];

    bookings.forEach(b => {
      if (b.booking_status === 'cancelled') {
        cancelled.push(b);
      } else if (b.journey_date >= today) {
        upcoming.push(b);
      } else {
        completed.push(b);
      }
    });

    return res.json({
      success: true,
      total: bookings.length,
      bookings: {
        upcoming,
        completed,
        cancelled,
        all: bookings
      }
    });
  } catch (error) {
    console.error('[BookingController] getMyBookings error:', error);
    return res.status(500).json({ success: false, message: 'Failed to fetch bookings.' });
  }
}

/**
 * Get single booking details by ID
 */
async function getBookingById(req, res) {
  try {
    const { id } = req.params;
    const userId = req.user.userId;
    const userRole = req.user.role;

    let query = `
      SELECT bk.*, 
             s.schedule_id, s.journey_date, s.departure_time, s.arrival_time,
             b.bus_id, b.bus_name, b.bus_number, b.bus_type, b.amenities,
             r.source_city, r.destination_city, r.distance_km, r.duration_minutes,
             o.company_name as operator_name, o.phone as operator_phone,
             bs1.stop_name as boarding_point,
             bs2.stop_name as dropping_point,
             u.name as user_name, u.email as user_email, u.phone as user_phone,
             p.payment_status, p.payment_method, p.transaction_id, p.payment_date
      FROM bookings bk
      JOIN schedules s ON bk.schedule_id = s.schedule_id
      JOIN buses b ON s.bus_id = b.bus_id
      JOIN routes r ON s.route_id = r.route_id
      JOIN operators o ON b.operator_id = o.operator_id
      JOIN users u ON bk.user_id = u.user_id
      LEFT JOIN bus_stops bs1 ON bk.boarding_stop_id = bs1.stop_id
      LEFT JOIN bus_stops bs2 ON bk.dropping_stop_id = bs2.stop_id
      LEFT JOIN payments p ON bk.booking_id = p.booking_id
      WHERE bk.booking_id = ?
    `;

    const params = [id];

    // Non-admin/non-operator can only view their own booking
    if (userRole === 'customer') {
      query += ` AND bk.user_id = ?`;
      params.push(userId);
    }

    const [bookings] = await pool.query(query, params);

    if (bookings.length === 0) {
      return res.status(404).json({ success: false, message: 'Booking not found.' });
    }

    const booking = bookings[0];

    // Fetch passengers
    const [passengers] = await pool.query(
      `SELECT passenger_id, passenger_name, age, gender, seat_number, seat_id
       FROM passengers
       WHERE booking_id = ?`,
      [id]
    );

    booking.passengers = passengers;
    booking.seat_numbers = passengers.map(p => p.seat_number).join(', ');

    return res.json({
      success: true,
      booking
    });
  } catch (error) {
    console.error('[BookingController] getBookingById error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve booking.' });
  }
}

/**
 * Cancel a booking and calculate refund
 */
async function cancelBooking(req, res) {
  const connection = await pool.getConnection();
  try {
    const { id } = req.params;
    const { reason = 'Customer requested cancellation' } = req.body;
    const userId = req.user.userId;

    await connection.beginTransaction();

    // 1. Fetch booking
    const [bookings] = await connection.query(
      `SELECT bk.*, s.journey_date, s.departure_time, s.schedule_id
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       WHERE bk.booking_id = ? AND bk.user_id = ? FOR UPDATE`,
      [id, userId]
    );

    if (bookings.length === 0) {
      await connection.rollback();
      return res.status(404).json({ success: false, message: 'Booking not found.' });
    }

    const booking = bookings[0];

    if (booking.booking_status === 'cancelled') {
      await connection.rollback();
      return res.status(400).json({ success: false, message: 'Booking is already cancelled.' });
    }

    // 2. Calculate Refund
    const refundDetails = calculateRefund(
      booking.journey_date,
      booking.departure_time,
      booking.total_amount
    );

    // 3. Update Booking Status
    await connection.query(
      `UPDATE bookings SET booking_status = 'cancelled' WHERE booking_id = ?`,
      [id]
    );

    // 4. Fetch passenger seats
    const [passengers] = await connection.query(
      `SELECT seat_id FROM passengers WHERE booking_id = ?`,
      [id]
    );

    const seatIds = passengers.map(p => p.seat_id);

    // 5. Release seats back to 'available'
    if (seatIds.length > 0) {
      await connection.query(
        `UPDATE seat_availability 
         SET status = 'available', locked_until = NULL, locked_by = NULL 
         WHERE schedule_id = ? AND seat_id IN (?)`,
        [booking.schedule_id, seatIds]
      );

      // Increase available seats on schedule
      await connection.query(
        `UPDATE schedules SET available_seats = available_seats + ? WHERE schedule_id = ?`,
        [seatIds.length, booking.schedule_id]
      );
    }

    // 6. Record Cancellation
    await connection.query(
      `INSERT INTO cancellations 
        (booking_id, cancellation_date, refund_amount, cancellation_charges, refund_status, reason, processed_at)
       VALUES (?, NOW(), ?, ?, 'processed', ?, NOW())`,
      [id, refundDetails.refundAmount, refundDetails.cancellationCharges, reason]
    );

    // 7. Update Payment status to refunded
    await connection.query(
      `UPDATE payments SET payment_status = 'refunded' WHERE booking_id = ?`,
      [id]
    );

    await connection.commit();

    // Send cancellation email in background
    sendCancellationEmail(req.user.email, {
      pnr: booking.pnr_number,
      refundAmount: refundDetails.refundAmount,
      cancellationCharges: refundDetails.cancellationCharges
    }).catch(err => console.error('[BookingController] Cancellation email error:', err.message));

    return res.json({
      success: true,
      message: 'Booking cancelled successfully.',
      refund: refundDetails
    });
  } catch (error) {
    await connection.rollback();
    console.error('[BookingController] cancelBooking error:', error);
    return res.status(500).json({ success: false, message: 'Failed to cancel booking.' });
  } finally {
    connection.release();
  }
}

module.exports = {
  lockSeats,
  validateCoupon,
  createBooking,
  getMyBookings,
  getBookingById,
  cancelBooking
};
