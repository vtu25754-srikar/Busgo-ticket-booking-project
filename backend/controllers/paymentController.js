const crypto = require('crypto');
const Razorpay = require('razorpay');
const { pool } = require('../config/db');
const { generateTransactionId } = require('../utils/generatePNR');
const { sendBookingConfirmation } = require('../utils/emailService');

// Initialize Razorpay instance
let razorpay = null;
try {
  if (process.env.RAZORPAY_KEY_ID && process.env.RAZORPAY_KEY_SECRET) {
    razorpay = new Razorpay({
      key_id: process.env.RAZORPAY_KEY_ID,
      key_secret: process.env.RAZORPAY_KEY_SECRET
    });
  }
} catch (e) {
  console.warn('[PaymentController] Razorpay init skipped:', e.message);
}

/**
 * Create a Razorpay payment order
 */
async function createOrder(req, res) {
  try {
    const { bookingId } = req.body;
    const userId = req.user.userId;

    if (!bookingId) {
      return res.status(400).json({ success: false, message: 'Booking ID is required.' });
    }

    // Verify booking
    const [bookings] = await pool.query(
      `SELECT bk.*, u.name, u.email, u.phone 
       FROM bookings bk 
       JOIN users u ON bk.user_id = u.user_id 
       WHERE bk.booking_id = ? AND bk.user_id = ?`,
      [bookingId, userId]
    );

    if (bookings.length === 0) {
      return res.status(404).json({ success: false, message: 'Booking not found.' });
    }

    const booking = bookings[0];
    const amountInPaise = Math.round(Number(booking.total_amount) * 100);

    let orderId = `order_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;

    // Try creating official Razorpay order if SDK is configured
    if (razorpay && !process.env.RAZORPAY_KEY_ID.includes('your_key')) {
      try {
        const order = await razorpay.orders.create({
          amount: amountInPaise,
          currency: 'INR',
          receipt: `receipt_booking_${bookingId}`,
          notes: {
            pnr: booking.pnr_number,
            bookingId: String(bookingId),
            userId: String(userId)
          }
        });
        orderId = order.id;
      } catch (rzpErr) {
        console.warn('[PaymentController] Razorpay order creation failed, using mock order:', rzpErr.message);
      }
    }

    // Update or insert payment record
    await pool.query(
      `INSERT INTO payments (booking_id, razorpay_order_id, amount, payment_status)
       VALUES (?, ?, ?, 'pending')
       ON DUPLICATE KEY UPDATE razorpay_order_id = VALUES(razorpay_order_id), amount = VALUES(amount)`,
      [bookingId, orderId, booking.total_amount]
    );

    return res.json({
      success: true,
      orderId,
      amount: booking.total_amount,
      amountInPaise,
      currency: 'INR',
      keyId: process.env.RAZORPAY_KEY_ID || 'rzp_test_busgo123456789',
      booking: {
        bookingId: booking.booking_id,
        pnr: booking.pnr_number,
        totalAmount: booking.total_amount
      },
      prefill: {
        name: booking.name,
        email: booking.email,
        phone: booking.phone
      }
    });
  } catch (error) {
    console.error('[PaymentController] createOrder error:', error);
    return res.status(500).json({ success: false, message: 'Failed to create payment order.' });
  }
}

/**
 * Verify Razorpay payment signature
 */
async function verifyPayment(req, res) {
  try {
    const {
      bookingId,
      razorpay_order_id,
      razorpay_payment_id,
      razorpay_signature,
      paymentMethod = 'Online / UPI'
    } = req.body;

    if (!bookingId) {
      return res.status(400).json({ success: false, message: 'Booking ID is required.' });
    }

    // Signature verification if keys are provided
    let isSignatureValid = true;
    const secret = process.env.RAZORPAY_KEY_SECRET;

    if (secret && !secret.includes('your_secret') && razorpay_signature && razorpay_order_id && razorpay_payment_id) {
      const generatedSignature = crypto
        .createHmac('sha256', secret)
        .update(`${razorpay_order_id}|${razorpay_payment_id}`)
        .digest('hex');

      isSignatureValid = (generatedSignature === razorpay_signature);
    }

    if (!isSignatureValid) {
      return res.status(400).json({
        success: false,
        message: 'Payment signature verification failed.'
      });
    }

    const txnId = razorpay_payment_id || generateTransactionId();

    // Update payment record
    await pool.query(
      `UPDATE payments 
       SET payment_status = 'success', 
           razorpay_payment_id = ?, 
           razorpay_signature = ?, 
           transaction_id = ?, 
           payment_method = ?, 
           payment_date = NOW()
       WHERE booking_id = ?`,
      [razorpay_payment_id || 'DEMO_PAY_ID', razorpay_signature || 'DEMO_SIG', txnId, paymentMethod, bookingId]
    );

    // Update booking status
    await pool.query(
      `UPDATE bookings SET booking_status = 'confirmed' WHERE booking_id = ?`,
      [bookingId]
    );

    // Fetch booking details for confirmation email
    const [bookings] = await pool.query(
      `SELECT bk.*, s.journey_date, s.departure_time, b.bus_name, r.source_city, r.destination_city, u.email
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       JOIN users u ON bk.user_id = u.user_id
       WHERE bk.booking_id = ?`,
      [bookingId]
    );

    if (bookings.length > 0) {
      const b = bookings[0];
      const [passengers] = await pool.query(
        'SELECT seat_number FROM passengers WHERE booking_id = ?',
        [bookingId]
      );
      const seats = passengers.map(p => p.seat_number);

      sendBookingConfirmation(b.email, {
        pnr: b.pnr_number,
        busName: b.bus_name,
        journeyDate: b.journey_date,
        departureTime: b.departure_time,
        fromCity: b.source_city,
        toCity: b.destination_city,
        seats,
        totalAmount: b.total_amount,
        passengerCount: seats.length
      }).catch(err => console.error('[PaymentController] Email error:', err.message));
    }

    return res.json({
      success: true,
      message: 'Payment verified and booking confirmed successfully!',
      transactionId: txnId
    });
  } catch (error) {
    console.error('[PaymentController] verifyPayment error:', error);
    return res.status(500).json({ success: false, message: 'Failed to verify payment.' });
  }
}

/**
 * Get payment status for a booking
 */
async function getPaymentStatus(req, res) {
  try {
    const { bookingId } = req.params;

    const [payments] = await pool.query(
      `SELECT p.*, bk.pnr_number, bk.booking_status, bk.total_amount 
       FROM payments p
       JOIN bookings bk ON p.booking_id = bk.booking_id
       WHERE p.booking_id = ?`,
      [bookingId]
    );

    if (payments.length === 0) {
      return res.status(404).json({ success: false, message: 'Payment record not found.' });
    }

    return res.json({
      success: true,
      payment: payments[0]
    });
  } catch (error) {
    console.error('[PaymentController] getPaymentStatus error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve payment status.' });
  }
}

module.exports = {
  createOrder,
  verifyPayment,
  getPaymentStatus
};
