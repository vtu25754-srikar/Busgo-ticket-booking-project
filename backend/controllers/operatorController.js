const { pool } = require('../config/db');

/**
 * Helper to resolve operator_id from req.user
 */
async function resolveOperatorId(user) {
  if (user.operatorId) return user.operatorId;
  const [rows] = await pool.query(
    'SELECT operator_id FROM operators WHERE user_id = ? LIMIT 1',
    [user.userId]
  );
  return rows.length > 0 ? rows[0].operator_id : null;
}

/**
 * Get Operator Dashboard statistics
 */
async function getDashboard(req, res) {
  try {
    const operatorId = await resolveOperatorId(req.user);
    if (!operatorId) {
      return res.status(403).json({ success: false, message: 'Operator account not found.' });
    }

    // Total buses
    const [[{ totalBuses }]] = await pool.query(
      `SELECT COUNT(*) as totalBuses FROM buses WHERE operator_id = ? AND is_active = 1`,
      [operatorId]
    );

    // Total bookings on this operator's buses
    const [[{ totalBookings }]] = await pool.query(
      `SELECT COUNT(DISTINCT bk.booking_id) as totalBookings 
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       WHERE b.operator_id = ? AND bk.booking_status = 'confirmed'`,
      [operatorId]
    );

    // Total revenue
    const [[{ totalRevenue }]] = await pool.query(
      `SELECT COALESCE(SUM(bk.total_amount), 0) as totalRevenue 
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       WHERE b.operator_id = ? AND bk.booking_status = 'confirmed'`,
      [operatorId]
    );

    // Upcoming schedules count
    const [[{ upcomingTrips }]] = await pool.query(
      `SELECT COUNT(*) as upcomingTrips 
       FROM schedules s
       JOIN buses b ON s.bus_id = b.bus_id
       WHERE b.operator_id = ? AND s.journey_date >= CURDATE() AND s.status = 'scheduled'`,
      [operatorId]
    );

    // Recent Bookings for this operator
    const [recentBookings] = await pool.query(
      `SELECT bk.booking_id, bk.pnr_number, bk.total_amount, bk.created_at,
              s.journey_date, s.departure_time,
              b.bus_name, b.bus_number,
              r.source_city, r.destination_city,
              u.name as customer_name, u.phone as customer_phone
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       JOIN users u ON bk.user_id = u.user_id
       WHERE b.operator_id = ? AND bk.booking_status = 'confirmed'
       ORDER BY bk.created_at DESC
       LIMIT 10`,
      [operatorId]
    );

    return res.json({
      success: true,
      stats: {
        totalBuses: Number(totalBuses),
        totalBookings: Number(totalBookings),
        totalRevenue: Number(totalRevenue),
        upcomingTrips: Number(upcomingTrips)
      },
      recentBookings
    });
  } catch (error) {
    console.error('[OperatorController] getDashboard error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve operator stats.' });
  }
}

/**
 * Get all buses belonging to this operator
 */
async function getMyBuses(req, res) {
  try {
    const operatorId = await resolveOperatorId(req.user);
    if (!operatorId) {
      return res.status(403).json({ success: false, message: 'Operator account not found.' });
    }

    const [buses] = await pool.query(
      `SELECT b.*, COUNT(DISTINCT s.schedule_id) as active_schedules
       FROM buses b
       LEFT JOIN schedules s ON b.bus_id = s.bus_id AND s.journey_date >= CURDATE()
       WHERE b.operator_id = ?
       GROUP BY b.bus_id
       ORDER BY b.created_at DESC`,
      [operatorId]
    );

    return res.json({ success: true, buses });
  } catch (error) {
    console.error('[OperatorController] getMyBuses error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve buses.' });
  }
}

/**
 * Add a new bus and automatically generate its seat layout
 */
async function addBus(req, res) {
  const connection = await pool.getConnection();
  try {
    const operatorId = await resolveOperatorId(req.user);
    if (!operatorId) {
      return res.status(403).json({ success: false, message: 'Operator account not found.' });
    }

    const {
      busName,
      busNumber,
      busType = 'AC_SEATER',
      totalSeats = 40,
      amenities = 'Charging Point, Water Bottle',
      description = ''
    } = req.body;

    if (!busName || !busNumber) {
      return res.status(400).json({ success: false, message: 'Bus name and bus number are required.' });
    }

    await connection.beginTransaction();

    // Check duplicate bus number
    const [existing] = await connection.query(
      `SELECT bus_id FROM buses WHERE bus_number = ? LIMIT 1`,
      [busNumber.trim().toUpperCase()]
    );

    if (existing.length > 0) {
      await connection.rollback();
      return res.status(409).json({ success: false, message: 'A bus with this registration number already exists.' });
    }

    // Insert Bus
    const [busResult] = await connection.query(
      `INSERT INTO buses (operator_id, bus_name, bus_number, bus_type, total_seats, amenities, description)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [operatorId, busName.trim(), busNumber.trim().toUpperCase(), busType, parseInt(totalSeats, 10), amenities, description]
    );

    const busId = busResult.insertId;

    // Generate Seats based on bus type
    const count = parseInt(totalSeats, 10);
    const isSleeper = busType.includes('SLEEPER');

    if (isSleeper) {
      // Half lower deck, half upper deck
      const half = Math.floor(count / 2);
      for (let i = 1; i <= half; i++) {
        await connection.query(
          `INSERT INTO seats (bus_id, seat_number, seat_type, deck, is_female_only)
           VALUES (?, ?, 'lower_berth', 'lower', ?)`,
          [busId, `L${i}`, i <= 2 ? 1 : 0]
        );
      }
      for (let i = 1; i <= (count - half); i++) {
        await connection.query(
          `INSERT INTO seats (bus_id, seat_number, seat_type, deck, is_female_only)
           VALUES (?, ?, 'upper_berth', 'upper', ?)`,
          [busId, `U${i}`, i <= 2 ? 1 : 0]
        );
      }
    } else {
      // Seater layout: A1, A2, ...
      for (let i = 1; i <= count; i++) {
        await connection.query(
          `INSERT INTO seats (bus_id, seat_number, seat_type, deck, is_female_only)
           VALUES (?, ?, 'seater', 'single', ?)`,
          [busId, `A${i}`, i <= 4 ? 1 : 0]
        );
      }
    }

    await connection.commit();

    return res.status(201).json({
      success: true,
      message: `Bus "${busName}" registered with ${count} seats!`,
      busId
    });
  } catch (error) {
    await connection.rollback();
    console.error('[OperatorController] addBus error:', error);
    return res.status(500).json({ success: false, message: 'Failed to add bus.' });
  } finally {
    connection.release();
  }
}

/**
 * Add a new schedule for a bus
 * Generates initial seat_availability records for all seats
 */
async function addSchedule(req, res) {
  const connection = await pool.getConnection();
  try {
    const operatorId = await resolveOperatorId(req.user);
    const { busId, routeId, journeyDate, departureTime, arrivalTime, ticketPrice } = req.body;

    if (!busId || !routeId || !journeyDate || !departureTime || !arrivalTime || !ticketPrice) {
      return res.status(400).json({ success: false, message: 'All schedule fields are required.' });
    }

    await connection.beginTransaction();

    // Verify bus ownership
    const [buses] = await connection.query(
      `SELECT bus_id, total_seats FROM buses WHERE bus_id = ? AND operator_id = ?`,
      [busId, operatorId]
    );

    if (buses.length === 0) {
      await connection.rollback();
      return res.status(403).json({ success: false, message: 'Bus not found or does not belong to you.' });
    }

    const totalSeats = buses[0].total_seats;

    // Insert schedule
    const [schedResult] = await connection.query(
      `INSERT INTO schedules 
        (bus_id, route_id, journey_date, departure_time, arrival_time, ticket_price, available_seats, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')`,
      [busId, routeId, journeyDate, departureTime, arrivalTime, ticketPrice, totalSeats]
    );

    const scheduleId = schedResult.insertId;

    // Fetch all seats for this bus
    const [seats] = await connection.query(
      `SELECT seat_id FROM seats WHERE bus_id = ?`,
      [busId]
    );

    // Insert seat_availability records
    for (const seat of seats) {
      await connection.query(
        `INSERT INTO seat_availability (seat_id, schedule_id, status)
         VALUES (?, ?, 'available')`,
        [seat.seat_id, scheduleId]
      );
    }

    await connection.commit();

    return res.status(201).json({
      success: true,
      message: 'Bus schedule added successfully!',
      scheduleId
    });
  } catch (error) {
    await connection.rollback();
    console.error('[OperatorController] addSchedule error:', error);
    return res.status(500).json({ success: false, message: 'Failed to add schedule.' });
  } finally {
    connection.release();
  }
}

/**
 * Add a new route
 */
async function addRoute(req, res) {
  try {
    const { sourceCity, destinationCity, distanceKm, durationMinutes } = req.body;

    if (!sourceCity || !destinationCity) {
      return res.status(400).json({ success: false, message: 'Source and destination cities are required.' });
    }

    const [result] = await pool.query(
      `INSERT INTO routes (source_city, destination_city, distance_km, duration_minutes)
       VALUES (?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE distance_km = VALUES(distance_km), duration_minutes = VALUES(duration_minutes)`,
      [sourceCity.trim(), destinationCity.trim(), distanceKm || 400, durationMinutes || 480]
    );

    return res.status(201).json({
      success: true,
      message: 'Route added successfully!',
      routeId: result.insertId
    });
  } catch (error) {
    console.error('[OperatorController] addRoute error:', error);
    return res.status(500).json({ success: false, message: 'Failed to add route.' });
  }
}

/**
 * Get all routes
 */
async function getAllRoutes(req, res) {
  try {
    const [routes] = await pool.query(
      `SELECT * FROM routes WHERE is_active = 1 ORDER BY source_city ASC`
    );
    return res.json({ success: true, routes });
  } catch (error) {
    console.error('[OperatorController] getAllRoutes error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve routes.' });
  }
}

/**
 * Get bookings for this operator
 */
async function getMyBookings(req, res) {
  try {
    const operatorId = await resolveOperatorId(req.user);
    if (!operatorId) {
      return res.status(403).json({ success: false, message: 'Operator account not found.' });
    }

    const [bookings] = await pool.query(
      `SELECT bk.booking_id, bk.pnr_number, bk.total_amount, bk.booking_status, bk.created_at,
              s.journey_date, s.departure_time,
              b.bus_name, b.bus_number,
              r.source_city, r.destination_city,
              u.name as customer_name, u.phone as customer_phone, u.email as customer_email,
              GROUP_CONCAT(ps.seat_number SEPARATOR ', ') as seats_booked
       FROM bookings bk
       JOIN schedules s ON bk.schedule_id = s.schedule_id
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       JOIN users u ON bk.user_id = u.user_id
       LEFT JOIN passengers ps ON bk.booking_id = ps.booking_id
       WHERE b.operator_id = ?
       GROUP BY bk.booking_id
       ORDER BY bk.created_at DESC`,
      [operatorId]
    );

    return res.json({ success: true, bookings });
  } catch (error) {
    console.error('[OperatorController] getMyBookings error:', error);
    return res.status(500).json({ success: false, message: 'Failed to retrieve bookings.' });
  }
}

module.exports = {
  getDashboard,
  getMyBuses,
  addBus,
  addSchedule,
  addRoute,
  getAllRoutes,
  getMyBookings
};
