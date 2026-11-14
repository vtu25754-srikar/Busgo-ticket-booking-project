const { pool } = require('../config/db');

/**
 * Get comprehensive admin dashboard statistics
 */
async function getDashboardStats(req, res) {
  try {
    // 1. Total customers
    const [[{ totalCustomers }]] = await pool.query(
      `SELECT COUNT(*) as totalCustomers FROM users WHERE role = 'customer'`
    );

    // 2. Total operators
    const [[{ totalOperators }]] = await pool.query(
      `SELECT COUNT(*) as totalOperators FROM operators`
    );

    // 3. Total buses
    const [[{ totalBuses }]] = await pool.query(
      `SELECT COUNT(*) as totalBuses FROM buses WHERE is_active = 1`
    );

    // 4. Total confirmed bookings
    const [[{ totalBookings }]] = await pool.query(
      `SELECT COUNT(*) as totalBookings FROM bookings WHERE booking_status = 'confirmed'`
    );

    // 5. Total revenue
    const [[{ totalRevenue }]] = await pool.query(
      `SELECT COALESCE(SUM(amount), 0) as totalRevenue FROM payments WHERE payment_status = 'success'`
    );

    // 6. Cancelled bookings
    const [[{ cancelledBookings }]] = await pool.query(
      `SELECT COUNT(*) as cancelledBookings FROM bookings WHERE booking_status = 'cancelled'`
    );

    // 7. Monthly bookings and revenue (last 6 months)
    const [monthlyStats] = await pool.query(
      `SELECT 
         DATE_FORMAT(b.created_at, '%b %Y') as month,
         COUNT(b.booking_id) as bookings,
         COALESCE(SUM(CASE WHEN b.booking_status = 'confirmed' THEN b.total_amount ELSE 0 END), 0) as revenue
       FROM bookings b
       WHERE b.created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
       GROUP BY DATE_FORMAT(b.created_at, '%Y-%m'), month
       ORDER BY DATE_FORMAT(b.created_at, '%Y-%m') ASC`
    );

    // 8. Popular travel routes
    const [popularRoutes] = await pool.query(
      `SELECT r.source_city, r.destination_city, COUNT(bk.booking_id) as booking_count,
              COALESCE(SUM(bk.total_amount), 0) as total_revenue
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN routes r ON s.route_id = r.route_id
       WHERE bk.booking_status = 'confirmed'
       GROUP BY r.route_id
       ORDER BY booking_count DESC
       LIMIT 5`
    );

    // 9. Recent Bookings (last 10)
    const [recentBookings] = await pool.query(
      `SELECT bk.booking_id, bk.pnr_number, bk.total_amount, bk.booking_status, bk.created_at,
              u.name as customer_name, u.email as customer_email,
              r.source_city, r.destination_city,
              b.bus_name
       FROM bookings bk
       JOIN users u ON bk.user_id = u.user_id
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       ORDER BY bk.created_at DESC
       LIMIT 10`
    );

    return res.json({
      success: true,
      stats: {
        totalCustomers: Number(totalCustomers),
        totalOperators: Number(totalOperators),
        totalBuses: Number(totalBuses),
        totalBookings: Number(totalBookings),
        totalRevenue: Number(totalRevenue),
        cancelledBookings: Number(cancelledBookings)
      },
      monthlyStats,
      popularRoutes,
      recentBookings
    });
  } catch (error) {
    console.error('[AdminController] getDashboardStats error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve admin stats.' });
  }
}

/**
 * Get paginated list of users
 */
async function getAllUsers(req, res) {
  try {
    const { role, search, page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    let query = `
      SELECT user_id, name, email, phone, role, is_active, created_at 
      FROM users WHERE 1=1
    `;
    const params = [];

    if (role) {
      query += ` AND role = ?`;
      params.push(role);
    }

    if (search) {
      query += ` AND (name LIKE ? OR email LIKE ? OR phone LIKE ?)`;
      params.push(`%${search}%`, `%${search}%`, `%${search}%`);
    }

    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(Number(limit), offset);

    const [users] = await pool.query(query, params);

    const [[{ total }]] = await pool.query(
      `SELECT COUNT(*) as total FROM users WHERE 1=1 ${role ? 'AND role = ?' : ''}`,
      role ? [role] : []
    );

    return res.json({
      success: true,
      users,
      pagination: {
        page: Number(page),
        limit: Number(limit),
        total,
        totalPages: Math.ceil(total / Number(limit))
      }
    });
  } catch (error) {
    console.error('[AdminController] getAllUsers error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve users.' });
  }
}

/**
 * Update user status (block or unblock)
 */
async function updateUserStatus(req, res) {
  try {
    const { id } = req.params;
    const { isActive } = req.body;

    await pool.query(
      `UPDATE users SET is_active = ? WHERE user_id = ?`,
      [isActive ? 1 : 0, id]
    );

    return res.json({
      success: true,
      message: `User account has been ${isActive ? 'activated' : 'deactivated'}.`
    });
  } catch (error) {
    console.error('[AdminController] updateUserStatus error:', error);
    return res.status(500).json({ success: false, message: 'Failed to update user status.' });
  }
}

/**
 * Get all bus operators
 */
async function getAllOperators(req, res) {
  try {
    const [operators] = await pool.query(
      `SELECT o.*, u.name as contact_person, u.is_active as user_active,
              COUNT(DISTINCT b.bus_id) as bus_count
       FROM operators o
       JOIN users u ON o.user_id = u.user_id
       LEFT JOIN buses b ON o.operator_id = b.operator_id
       GROUP BY o.operator_id
       ORDER BY o.created_at DESC`
    );

    return res.json({
      success: true,
      operators
    });
  } catch (error) {
    console.error('[AdminController] getAllOperators error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve operators.' });
  }
}

/**
 * Update operator approval status
 */
async function updateOperatorStatus(req, res) {
  try {
    const { id } = req.params;
    const { status } = req.body; // 'approved', 'rejected', 'suspended'

    if (!['pending', 'approved', 'rejected', 'suspended'].includes(status)) {
      return res.status(400).json({ success: false, message: 'Invalid status value.' });
    }

    await pool.query(
      `UPDATE operators SET status = ? WHERE operator_id = ?`,
      [status, id]
    );

    return res.json({
      success: true,
      message: `Operator status updated to "${status}".`
    });
  } catch (error) {
    console.error('[AdminController] updateOperatorStatus error:', error);
    return res.status(500).json({ success: false, message: 'Failed to update operator status.' });
  }
}

/**
 * Get all platform bookings
 */
async function getAllBookings(req, res) {
  try {
    const { status, pnr, page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    let query = `
      SELECT bk.booking_id, bk.pnr_number, bk.total_amount, bk.booking_status, bk.created_at,
             u.name as customer_name, u.email as customer_email, u.phone as customer_phone,
             s.journey_date, s.departure_time,
             b.bus_name, b.bus_number,
             r.source_city, r.destination_city,
             o.company_name as operator_name,
             p.payment_status, p.payment_method
      FROM bookings bk
      JOIN users u ON bk.user_id = u.user_id
      JOIN schedules s ON bk.schedule_id = s.schedule_id
      JOIN buses b ON s.bus_id = b.bus_id
      JOIN routes r ON s.route_id = r.route_id
      JOIN operators o ON b.operator_id = o.operator_id
      LEFT JOIN payments p ON bk.booking_id = p.booking_id
      WHERE 1=1
    `;
    const params = [];

    if (status) {
      query += ` AND bk.booking_status = ?`;
      params.push(status);
    }

    if (pnr) {
      query += ` AND bk.pnr_number LIKE ?`;
      params.push(`%${pnr.trim()}%`);
    }

    query += ` ORDER BY bk.created_at DESC LIMIT ? OFFSET ?`;
    params.push(Number(limit), offset);

    const [bookings] = await pool.query(query, params);

    return res.json({
      success: true,
      bookings
    });
  } catch (error) {
    console.error('[AdminController] getAllBookings error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve bookings.' });
  }
}

/**
 * Get all registered buses across operators
 */
async function getAllBuses(req, res) {
  try {
    const [buses] = await pool.query(
      `SELECT b.*, o.company_name as operator_name, o.phone as operator_phone
       FROM buses b
       JOIN operators o ON b.operator_id = o.operator_id
       ORDER BY b.created_at DESC`
    );

    return res.json({
      success: true,
      buses
    });
  } catch (error) {
    console.error('[AdminController] getAllBuses error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve buses.' });
  }
}

module.exports = {
  getDashboardStats,
  getAllUsers,
  updateUserStatus,
  getAllOperators,
  updateOperatorStatus,
  getAllBookings,
  getAllBuses
};
