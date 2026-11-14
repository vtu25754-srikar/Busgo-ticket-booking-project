/**
 * Calculate refund based on time difference between now and journey date/time
 * Cancellation Policy:
 *  - > 72 hours (3 days) before departure: 90% refund (10% charge)
 *  - 24 - 72 hours (1-3 days) before departure: 50% refund (50% charge)
 *  - < 24 hours before departure: 0% refund (100% charge)
 */
function calculateRefund(journeyDateStr, departureTimeStr, totalAmount) {
  try {
    const journeyDateTime = new Date(`${journeyDateStr}T${departureTimeStr || '00:00:00'}`);
    const now = new Date();
    const diffHours = (journeyDateTime - now) / (1000 * 60 * 60);

    let refundPercentage = 0;
    let policyText = '';

    if (diffHours >= 72) {
      refundPercentage = 0.90;
      policyText = 'More than 72 hours before departure (90% refund)';
    } else if (diffHours >= 24) {
      refundPercentage = 0.50;
      policyText = 'Between 24 to 72 hours before departure (50% refund)';
    } else {
      refundPercentage = 0.0;
      policyText = 'Less than 24 hours before departure (No refund applicable)';
    }

    const refundAmount = Math.round(Number(totalAmount) * refundPercentage * 100) / 100;
    const cancellationCharges = Math.round((Number(totalAmount) - refundAmount) * 100) / 100;

    return {
      refundAmount,
      cancellationCharges,
      refundPercentage: Math.round(refundPercentage * 100),
      policyText
    };
  } catch (err) {
    return {
      refundAmount: 0,
      cancellationCharges: Number(totalAmount),
      refundPercentage: 0,
      policyText: 'Standard cancellation policy applied'
    };
  }
}

/**
 * Release expired seat locks from seat_availability table
 */
async function releaseExpiredLocks(pool) {
  try {
    const [result] = await pool.query(
      `UPDATE seat_availability 
       SET status = 'available', locked_until = NULL, locked_by = NULL 
       WHERE status = 'locked' AND locked_until < NOW()`
    );
    if (result.affectedRows > 0) {
      console.log(`[BookingService] Released ${result.affectedRows} expired seat lock(s).`);
    }
  } catch (err) {
    console.error('[BookingService] Error releasing expired seat locks:', err.message);
  }
}

module.exports = {
  calculateRefund,
  releaseExpiredLocks
};
