const mysql = require('mysql2/promise');
const dotenv = require('dotenv');

dotenv.config();

// Create connection pool
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '3306', 10),
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'busgo_db',
  waitForConnections: true,
  connectionLimit: 15,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 10000,
  dateStrings: true
});

// Test database connection helper
async function testConnection() {
  try {
    const connection = await pool.getConnection();
    console.log(`[DB] Connected to MySQL database "${process.env.DB_NAME || 'busgo_db'}" successfully.`);
    connection.release();
    return true;
  } catch (error) {
    console.error('[DB] Database connection error:', error.message);
    return false;
  }
}

module.exports = {
  pool,
  testConnection
};
