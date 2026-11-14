const PDFDocument = require('pdfkit');

/**
 * Generate a high quality electronic bus ticket PDF stream/buffer
 * @param {Object} booking Complete booking object with schedule, bus, passenger and route info
 * @returns {Promise<Buffer>}
 */
function generateTicketPDF(booking) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        margin: 36,
        size: 'A4'
      });

      const buffers = [];
      doc.on('data', buffers.push.bind(buffers));
      doc.on('end', () => {
        const pdfData = Buffer.concat(buffers);
        resolve(pdfData);
      });

      // Colors
      const primaryRed = '#E2231A';
      const darkNavy = '#1A1A2E';
      const lightGrey = '#F8F9FA';
      const borderColor = '#DDE2E5';

      // --- Header Banner ---
      doc.rect(36, 36, 523, 70).fill(primaryRed);

      doc.fillColor('#FFFFFF')
         .fontSize(26)
         .font('Helvetica-Bold')
         .text('BUSGO', 50, 48);

      doc.fontSize(10)
         .font('Helvetica')
         .text('Electronic Bus Ticket & Travel Receipt', 50, 78);

      doc.fontSize(11)
         .font('Helvetica-Bold')
         .text(`PNR: ${booking.pnr_number || 'N/A'}`, 390, 50, { align: 'right', width: 155 });

      doc.fontSize(9)
         .font('Helvetica')
         .text(`Booking ID: #${booking.booking_id || ''}`, 390, 68, { align: 'right', width: 155 })
         .text(`Status: ${String(booking.booking_status || 'CONFIRMED').toUpperCase()}`, 390, 82, { align: 'right', width: 155 });

      let yPos = 120;

      // --- Journey Summary Box ---
      doc.rect(36, yPos, 523, 95).fillAndStroke(lightGrey, borderColor);

      doc.fillColor(darkNavy)
         .fontSize(14)
         .font('Helvetica-Bold')
         .text(`${booking.source_city || 'Origin'}   -->   ${booking.destination_city || 'Destination'}`, 50, yPos + 12);

      doc.fontSize(9).font('Helvetica').fillColor('#555555');
      doc.text(`Journey Date:`, 50, yPos + 35);
      doc.text(`Departure Time:`, 50, yPos + 50);
      doc.text(`Arrival Time:`, 50, yPos + 65);

      doc.font('Helvetica-Bold').fillColor(darkNavy);
      doc.text(`${booking.journey_date || 'N/A'}`, 150, yPos + 35);
      doc.text(`${booking.departure_time || 'N/A'}`, 150, yPos + 50);
      doc.text(`${booking.arrival_time || 'N/A'}`, 150, yPos + 65);

      doc.font('Helvetica').fillColor('#555555');
      doc.text(`Bus Operator:`, 310, yPos + 35);
      doc.text(`Bus Model:`, 310, yPos + 50);
      doc.text(`Bus Type:`, 310, yPos + 65);

      doc.font('Helvetica-Bold').fillColor(darkNavy);
      doc.text(`${booking.operator_name || booking.company_name || 'Sharma Travels'}`, 410, yPos + 35);
      doc.text(`${booking.bus_name || ''} (${booking.bus_number || ''})`, 410, yPos + 50);
      doc.text(`${booking.bus_type || 'AC Sleeper'}`, 410, yPos + 65);

      yPos += 115;

      // --- Boarding & Dropping Section ---
      doc.rect(36, yPos, 255, 60).stroke(borderColor);
      doc.rect(304, yPos, 255, 60).stroke(borderColor);

      doc.fontSize(9).font('Helvetica-Bold').fillColor(primaryRed)
         .text('BOARDING POINT', 46, yPos + 8);
      doc.fontSize(9).font('Helvetica').fillColor(darkNavy)
         .text(booking.boarding_point || `${booking.source_city} Central Bus Stand`, 46, yPos + 24, { width: 235 });

      doc.fontSize(9).font('Helvetica-Bold').fillColor(primaryRed)
         .text('DROPPING POINT', 314, yPos + 8);
      doc.fontSize(9).font('Helvetica').fillColor(darkNavy)
         .text(booking.dropping_point || `${booking.destination_city} Main Station`, 314, yPos + 24, { width: 235 });

      yPos += 75;

      // --- Passenger Details Table ---
      doc.fontSize(11).font('Helvetica-Bold').fillColor(darkNavy)
         .text('PASSENGER DETAILS', 36, yPos);
      yPos += 18;

      // Table Header
      doc.rect(36, yPos, 523, 22).fill('#E9ECEF');
      doc.fillColor(darkNavy).fontSize(9).font('Helvetica-Bold');
      doc.text('S.No', 46, yPos + 6);
      doc.text('Passenger Name', 90, yPos + 6);
      doc.text('Age', 280, yPos + 6);
      doc.text('Gender', 340, yPos + 6);
      doc.text('Seat No.', 420, yPos + 6);

      yPos += 22;

      // Table Rows
      const passengers = booking.passengers || [];
      if (passengers.length === 0) {
        doc.rect(36, yPos, 523, 22).stroke(borderColor);
        doc.font('Helvetica').text('1', 46, yPos + 6);
        doc.text(booking.passenger_name || booking.user_name || 'Primary Passenger', 90, yPos + 6);
        doc.text(String(booking.age || '28'), 280, yPos + 6);
        doc.text(booking.gender || 'Male', 340, yPos + 6);
        doc.font('Helvetica-Bold').fillColor(primaryRed).text(booking.seat_numbers || 'L1', 420, yPos + 6);
        yPos += 22;
      } else {
        passengers.forEach((p, idx) => {
          doc.rect(36, yPos, 523, 22).stroke(borderColor);
          doc.fillColor(darkNavy).font('Helvetica').fontSize(9);
          doc.text(String(idx + 1), 46, yPos + 6);
          doc.text(p.passenger_name || p.name || 'Passenger', 90, yPos + 6);
          doc.text(String(p.age || '-'), 280, yPos + 6);
          doc.text(String(p.gender || '-').toUpperCase(), 340, yPos + 6);
          doc.font('Helvetica-Bold').fillColor(primaryRed).text(p.seat_number || '-', 420, yPos + 6);
          yPos += 22;
        });
      }

      yPos += 15;

      // --- Fare Breakdown Box ---
      doc.fontSize(11).font('Helvetica-Bold').fillColor(darkNavy)
         .text('FARE & PAYMENT SUMMARY', 36, yPos);
      yPos += 18;

      doc.rect(36, yPos, 523, 75).stroke(borderColor);

      doc.fontSize(9).font('Helvetica').fillColor('#555555');
      doc.text('Base Bus Fare:', 50, yPos + 10);
      doc.text('Convenience & Platform Fee:', 50, yPos + 24);
      doc.text('GST & Travel Taxes (5%):', 50, yPos + 38);
      doc.text('Discount Applied:', 50, yPos + 52);

      const baseFare = Number(booking.total_amount || 1000) - Number(booking.convenience_fee || 50) - Number(booking.taxes || 45) + Number(booking.discount_amount || 0);
      doc.font('Helvetica').fillColor(darkNavy);
      doc.text(`Rs. ${Math.max(baseFare, 0).toFixed(2)}`, 220, yPos + 10);
      doc.text(`Rs. ${Number(booking.convenience_fee || 50).toFixed(2)}`, 220, yPos + 24);
      doc.text(`Rs. ${Number(booking.taxes || 45).toFixed(2)}`, 220, yPos + 38);
      doc.text(`- Rs. ${Number(booking.discount_amount || 0).toFixed(2)}`, 220, yPos + 52);

      // Vertical Divider & Total
      doc.moveTo(350, yPos).lineTo(350, yPos + 75).stroke(borderColor);

      doc.fontSize(10).font('Helvetica-Bold').fillColor(darkNavy)
         .text('TOTAL AMOUNT PAID', 370, yPos + 18);
      doc.fontSize(18).font('Helvetica-Bold').fillColor(primaryRed)
         .text(`Rs. ${Number(booking.total_amount || 0).toFixed(2)}`, 370, yPos + 36);

      yPos += 95;

      // --- Important Instructions ---
      doc.fontSize(10).font('Helvetica-Bold').fillColor(darkNavy)
         .text('IMPORTANT TRAVEL INFORMATION', 36, yPos);
      yPos += 16;

      const instructions = [
        '1. Please arrive at the boarding point at least 15-30 minutes before the scheduled departure time.',
        '2. Carrying a valid government-issued photo ID (Aadhaar/Driving License/Passport) is mandatory.',
        '3. This electronic ticket is valid for travel without a physical printout. Keep SMS/Email handy.',
        '4. Cancellation charges apply as per BUSGO refund policy (up to 90% refund if cancelled 3+ days in advance).',
        '5. For 24/7 customer support, call 1800-123-BUSGO or write to support@busgo.com.'
      ];

      doc.fontSize(8).font('Helvetica').fillColor('#555555');
      instructions.forEach((line) => {
        doc.text(line, 42, yPos, { width: 510 });
        yPos += 13;
      });

      // --- Footer ---
      doc.fontSize(8).font('Helvetica-Oblique').fillColor('#888888')
         .text('BUSGO Technologies India Pvt. Ltd. | www.busgo.com | Happy & Safe Journey!', 36, 770, { align: 'center', width: 523 });

      doc.end();
    } catch (err) {
      reject(err);
    }
  });
}

module.exports = {
  generateTicketPDF
};
