const nodemailer = require('nodemailer');
const dotenv = require('dotenv');

dotenv.config();

// Create transporter
let transporter = null;
try {
  transporter = nodemailer.createTransport({
    host: process.env.EMAIL_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.EMAIL_PORT || '587', 10),
    secure: false, // true for 465, false for other ports
    auth: {
      user: process.env.EMAIL_USER || '',
      pass: process.env.EMAIL_PASS || ''
    }
  });
} catch (e) {
  console.warn('[EmailService] SMTP Transporter initialization skipped:', e.message);
}

/**
 * Send welcome email on registration
 */
async function sendWelcomeEmail(to, name) {
  if (!transporter || !process.env.EMAIL_USER) {
    console.log(`[EmailService] (Simulated) Welcome email sent to: ${to} for user ${name}`);
    return;
  }
  try {
    await transporter.sendMail({
      from: `"BUSGO Travel" <${process.env.EMAIL_USER}>`,
      to,
      subject: 'Welcome to BUSGO – Your Journey Begins Here!',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #e2231a; text-align: center;">🚌 BUSGO</h2>
          <h3>Hello ${name},</h3>
          <p>Thank you for registering with <strong>BUSGO</strong> – India's premier online bus ticket booking platform.</p>
          <p>You can now search, compare and book bus tickets seamlessly across 10,000+ routes with real-time seat selection.</p>
          <p style="margin-top: 30px;">Happy Journey!<br><strong>Team BUSGO</strong></p>
        </div>
      `
    });
  } catch (error) {
    console.error('[EmailService] Failed to send welcome email:', error.message);
  }
}

/**
 * Send booking confirmation email
 */
async function sendBookingConfirmation(to, bookingDetails) {
  const { pnr, busName, journeyDate, departureTime, fromCity, toCity, seats, totalAmount, passengerCount } = bookingDetails;
  
  if (!transporter || !process.env.EMAIL_USER) {
    console.log(`[EmailService] (Simulated) Booking confirmation email sent to: ${to} for PNR: ${pnr}`);
    return;
  }

  try {
    await transporter.sendMail({
      from: `"BUSGO Bookings" <${process.env.EMAIL_USER}>`,
      to,
      subject: `Booking Confirmed! PNR: ${pnr} - BUSGO`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <div style="background-color: #e2231a; padding: 15px; border-radius: 6px; text-align: center; color: #ffffff;">
            <h1 style="margin: 0; font-size: 24px;">BUSGO E-TICKET CONFIRMATION</h1>
          </div>
          <div style="padding: 20px 0;">
            <p>Dear Passenger,</p>
            <p>Your bus booking has been <strong>successfully confirmed</strong>! Below are your journey details:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
              <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>PNR Number:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #e2231a; font-weight: bold; font-size: 16px;">${pnr}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Route:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">${fromCity} &rarr; ${toCity}</td>
              </tr>
              <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Bus Operator / Bus:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">${busName}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Journey Date & Time:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">${journeyDate} at ${departureTime}</td>
              </tr>
              <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Seat Number(s):</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">${Array.isArray(seats) ? seats.join(', ') : seats}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Amount Paid:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">₹${totalAmount}</td>
              </tr>
            </table>

            <p style="margin-top: 20px; font-size: 13px; color: #666;">
              Please carry a valid government ID during your journey. Show this e-ticket or SMS to the bus conductor before boarding.
            </p>
          </div>
          <div style="border-top: 1px solid #e0e0e0; padding-top: 15px; text-align: center; color: #888; font-size: 12px;">
            <p>BUSGO Customer Support: support@busgo.com | 1800-123-BUSGO</p>
          </div>
        </div>
      `
    });
  } catch (error) {
    console.error('[EmailService] Failed to send booking confirmation email:', error.message);
  }
}

/**
 * Send cancellation email
 */
async function sendCancellationEmail(to, cancellationDetails) {
  const { pnr, refundAmount, cancellationCharges } = cancellationDetails;
  
  if (!transporter || !process.env.EMAIL_USER) {
    console.log(`[EmailService] (Simulated) Cancellation email sent to: ${to} for PNR: ${pnr}`);
    return;
  }

  try {
    await transporter.sendMail({
      from: `"BUSGO Bookings" <${process.env.EMAIL_USER}>`,
      to,
      subject: `Ticket Cancelled - PNR: ${pnr} - BUSGO`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #e2231a;">Ticket Cancellation Notice</h2>
          <p>Your booking with <strong>PNR: ${pnr}</strong> has been cancelled upon your request.</p>
          <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr>
              <td style="padding: 8px; border: 1px solid #ddd;"><strong>Cancellation Fee:</strong></td>
              <td style="padding: 8px; border: 1px solid #ddd;">₹${cancellationCharges}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #ddd;"><strong>Refund Amount:</strong></td>
              <td style="padding: 8px; border: 1px solid #ddd; color: #28a745; font-weight: bold;">₹${refundAmount}</td>
            </tr>
          </table>
          <p>The refund amount will be credited to your original payment method within 5-7 business days.</p>
          <p>Team BUSGO</p>
        </div>
      `
    });
  } catch (error) {
    console.error('[EmailService] Failed to send cancellation email:', error.message);
  }
}

module.exports = {
  sendWelcomeEmail,
  sendBookingConfirmation,
  sendCancellationEmail
};
