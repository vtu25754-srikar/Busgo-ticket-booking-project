/**
 * Generate a unique PNR (Passenger Name Record)
 * Format: BG-YYYYMMDD-XXXX (e.g., BG-20261112-9A4B)
 */
function generatePNR() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let randomPart = '';
  for (let i = 0; i < 4; i++) {
    randomPart += chars.charAt(Math.floor(Math.random() * chars.length));
  }

  return `BG${year}${month}${day}${randomPart}`;
}

/**
 * Generate a transaction ID
 */
function generateTransactionId() {
  return `TXN_${Date.now()}_${Math.random().toString(36).substring(2, 7).toUpperCase()}`;
}

module.exports = {
  generatePNR,
  generateTransactionId
};
