const express = require('express');
const cors = require('cors');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const { testConnection, pool } = require('./config/db');
const { releaseExpiredLocks } = require('./services/bookingService');

// Route imports
const authRoutes = require('./routes/authRoutes');
const busRoutes = require('./routes/busRoutes');
const bookingRoutes = require('./routes/bookingRoutes');
const paymentRoutes = require('./routes/paymentRoutes');
const adminRoutes = require('./routes/adminRoutes');
const operatorRoutes = require('./routes/operatorRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS
app.use(cors({
  origin: '*', // Allow all origins for seamless development and testing
  credentials: true
}));

// Body parsers
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve frontend static assets directly from frontend directory
const frontendPath = path.join(__dirname, '../frontend');
app.use(express.static(frontendPath));

// API Health Check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    app: 'BUSGO - Online Bus Ticket Booking System',
    timestamp: new Date().toISOString()
  });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/buses', busRoutes);
app.use('/api/bookings', bookingRoutes);
app.use('/api/payments', paymentRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/operator', operatorRoutes);

// Catch-all route to serve index.html for frontend single-page navigation if not matched
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ success: false, message: 'API endpoint not found.' });
  }
  res.sendFile(path.join(frontendPath, 'index.html'), (err) => {
    if (err) next();
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('[ServerError]', err.stack || err.message);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || 'An unexpected internal server error occurred.'
  });
});

// Start Server and Test DB
app.listen(PORT, async () => {
  console.log(`====================================================`);
  console.log(`🚌 BUSGO Server running on http://localhost:${PORT}`);
  console.log(`🌍 Frontend available at: http://localhost:${PORT}`);
  console.log(`====================================================`);

  await testConnection();

  // Periodic cleanup of expired seat locks (every 2 minutes)
  setInterval(() => {
    releaseExpiredLocks(pool);
  }, 2 * 60 * 1000);
});

module.exports = app;
