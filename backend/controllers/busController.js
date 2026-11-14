const { pool } = require('../config/db');

/**
 * Search buses between two cities on a given date
 * Supports filtering by bus type, operator, price range, and sorting
 */
async function searchBuses(req, res) {
  try {
    const {
      from,
      to,
      date,
      passengers = 1,
      busType,
      operator,
      minPrice,
      maxPrice,
      sortBy = 'price_asc'
    } = req.query;

    if (!from || !to || !date) {
      return res.status(400).json({
        success: false,
        message: 'From city, to city, and journey date are required parameters.'
      });
    }

    let query = `
      SELECT s.schedule_id, s.journey_date, s.departure_time, s.arrival_time, 
             s.ticket_price, s.available_seats, s.status as schedule_status,
             b.bus_id, b.bus_name, b.bus_number, b.bus_type, b.total_seats, 
             b.amenities, b.rating, b.description,
             o.operator_id, o.company_name as operator_name, o.rating as operator_rating,
             r.route_id, r.source_city, r.destination_city, r.distance_km, r.duration_minutes
      FROM schedules s
      JOIN buses b ON s.bus_id = b.bus_id
      JOIN routes r ON s.route_id = r.route_id
      JOIN operators o ON b.operator_id = o.operator_id
      WHERE LOWER(r.source_city) = LOWER(?)
        AND LOWER(r.destination_city) = LOWER(?)
        AND s.journey_date = ?
        AND s.status = 'scheduled'
        AND b.is_active = 1
        AND o.status = 'approved'
    `;

    const queryParams = [from.trim(), to.trim(), date.trim()];

    // Filter by available seats
    if (Number(passengers) > 1) {
      query += ` AND s.available_seats >= ?`;
      queryParams.push(Number(passengers));
    }

    // Filter by bus type
    if (busType) {
      const types = Array.isArray(busType) ? busType : [busType];
      query += ` AND b.bus_type IN (${types.map(() => '?').join(',')})`;
      types.forEach(t => queryParams.push(t));
    }

    // Filter by operator
    if (operator) {
      query += ` AND LOWER(o.company_name) LIKE LOWER(?)`;
      queryParams.push(`%${operator.trim()}%`);
    }

    // Filter by price range
    if (minPrice) {
      query += ` AND s.ticket_price >= ?`;
      queryParams.push(Number(minPrice));
    }
    if (maxPrice) {
      query += ` AND s.ticket_price <= ?`;
      queryParams.push(Number(maxPrice));
    }

    // Sorting
    switch (sortBy) {
      case 'price_desc':
        query += ` ORDER BY s.ticket_price DESC`;
        break;
      case 'rating_desc':
        query += ` ORDER BY b.rating DESC, s.ticket_price ASC`;
        break;
      case 'departure_asc':
        query += ` ORDER BY s.departure_time ASC`;
        break;
      case 'departure_desc':
        query += ` ORDER BY s.departure_time DESC`;
        break;
      case 'duration_asc':
        query += ` ORDER BY r.duration_minutes ASC`;
        break;
      case 'price_asc':
      default:
        query += ` ORDER BY s.ticket_price ASC`;
        break;
    }

    const [buses] = await pool.query(query, queryParams);

    // Format results with computed duration, tags and formatted times
    const formattedBuses = buses.map(bus => {
      const durationMinutes = bus.duration_minutes || 480;
      const durationHours = Math.floor(durationMinutes / 60);
      const durationMins = durationMinutes % 60;
      const durationText = `${durationHours}h ${durationMins > 0 ? durationMins + 'm' : ''}`.trim();

      const amenitiesList = bus.amenities 
        ? bus.amenities.split(',').map(a => a.trim()) 
        : ['Charging Point', 'Water Bottle', 'Blanket'];

      // --- Dynamic arrival time calculation ---
      // Parse departure_time (HH:MM:SS or HH:MM string from MySQL TIME column)
      let depTimeStr = bus.departure_time || '00:00:00';
      // MySQL TIME can come as a string or numeric; normalize it
      if (typeof depTimeStr !== 'string') depTimeStr = String(depTimeStr);
      const depParts = depTimeStr.split(':');
      const depHour = parseInt(depParts[0], 10) || 0;
      const depMin = parseInt(depParts[1], 10) || 0;

      // Total departure minutes from midnight
      const depTotalMins = depHour * 60 + depMin;
      // Add journey duration
      const arrTotalMins = depTotalMins + durationMinutes;
      // Compute arrival hour/minute (may exceed 24h = next day)
      const arrHour = Math.floor(arrTotalMins / 60) % 24;
      const arrMin = arrTotalMins % 60;
      const crossesMidnight = arrTotalMins >= 1440; // 1440 = 24 * 60

      // Format arrival_time as HH:MM:SS for the frontend formatTime() function
      const computedArrivalTime = `${String(arrHour).padStart(2, '0')}:${String(arrMin).padStart(2, '0')}:00`;

      return {
        ...bus,
        arrival_time: computedArrivalTime,
        arrival_next_day: crossesMidnight,
        duration_text: durationText,
        amenities_list: amenitiesList,
        is_ac: bus.bus_type.includes('AC'),
        is_sleeper: bus.bus_type.includes('SLEEPER')
      };
    });

    return res.json({
      success: true,
      count: formattedBuses.length,
      searchCriteria: {
        from: from.trim(),
        to: to.trim(),
        date: date.trim(),
        passengers: Number(passengers)
      },
      buses: formattedBuses
    });
  } catch (error) {
    console.error('[BusController] searchBuses error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to search buses.'
    });
  }
}

/**
 * Get distinct list of cities from active routes
 */
async function getAllCities(req, res) {
  try {
    const [sourceCities] = await pool.query(
      `SELECT DISTINCT source_city as city FROM routes WHERE is_active = 1`
    );
    const [destCities] = await pool.query(
      `SELECT DISTINCT destination_city as city FROM routes WHERE is_active = 1`
    );

    const citySet = new Set();
    sourceCities.forEach(r => citySet.add(r.city));
    destCities.forEach(r => citySet.add(r.city));

    const cities = Array.from(citySet).sort();

    return res.json({
      success: true,
      cities
    });
  } catch (error) {
    console.error('[BusController] getAllCities error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to retrieve cities.'
    });
  }
}

/**
 * Get bus details including route stops
 */
async function getBusDetails(req, res) {
  try {
    const { id } = req.params;

    const [buses] = await pool.query(
      `SELECT b.*, o.company_name as operator_name, o.phone as operator_phone, o.email as operator_email
       FROM buses b
       JOIN operators o ON b.operator_id = o.operator_id
       WHERE b.bus_id = ?`,
      [id]
    );

    if (buses.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Bus not found.'
      });
    }

    const bus = buses[0];

    // Fetch reviews
    const [reviews] = await pool.query(
      `SELECT r.*, u.name as user_name 
       FROM reviews r 
       JOIN users u ON r.user_id = u.user_id 
       WHERE r.bus_id = ? 
       ORDER BY r.created_at DESC LIMIT 10`,
      [id]
    );

    return res.json({
      success: true,
      bus: {
        ...bus,
        reviews
      }
    });
  } catch (error) {
    console.error('[BusController] getBusDetails error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to retrieve bus details.'
    });
  }
}

/**
 * Get seat layout and live availability for a schedule
 */
async function getScheduleSeats(req, res) {
  try {
    const { scheduleId } = req.params;

    // Fetch schedule and bus info
    const [schedules] = await pool.query(
      `SELECT s.*, b.bus_id, b.bus_name, b.bus_type, b.total_seats,
              r.source_city, r.destination_city, r.route_id,
              o.company_name as operator_name
       FROM schedules s
       JOIN buses b ON s.bus_id = b.bus_id
       JOIN routes r ON s.route_id = r.route_id
       JOIN operators o ON b.operator_id = o.operator_id
       WHERE s.schedule_id = ?`,
      [scheduleId]
    );

    if (schedules.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Schedule not found.'
      });
    }

    const schedule = schedules[0];

    // Fetch all seats for the bus with availability status for this schedule
    const [seats] = await pool.query(
      `SELECT se.seat_id, se.bus_id, se.seat_number, se.seat_type, se.deck, se.is_female_only,
              COALESCE(sa.status, 'available') as status,
              sa.locked_until,
              sa.locked_by
       FROM seats se
       LEFT JOIN seat_availability sa 
         ON se.seat_id = sa.seat_id AND sa.schedule_id = ?
       WHERE se.bus_id = ?
       ORDER BY se.deck ASC, CAST(SUBSTRING(se.seat_number, 2) AS UNSIGNED), se.seat_number ASC`,
      [scheduleId, schedule.bus_id]
    );

    // Fetch boarding and dropping points for this route
    const [stops] = await pool.query(
      `SELECT stop_id, stop_name, stop_type, sequence_order, landmark
       FROM bus_stops
       WHERE route_id = ?
       ORDER BY sequence_order ASC`,
      [schedule.route_id]
    );

    const boardingStops = stops.filter(s => s.stop_type === 'boarding' || s.stop_type === 'both');
    const droppingStops = stops.filter(s => s.stop_type === 'dropping' || s.stop_type === 'both');

    // Group seats by deck
    const lowerDeck = seats.filter(s => s.deck === 'lower' || s.deck === 'single');
    const upperDeck = seats.filter(s => s.deck === 'upper');

    return res.json({
      success: true,
      schedule,
      seats,
      decks: {
        hasUpperDeck: upperDeck.length > 0,
        lowerDeck,
        upperDeck
      },
      stops: {
        boarding: boardingStops,
        dropping: droppingStops
      }
    });
  } catch (error) {
    console.error('[BusController] getScheduleSeats error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to retrieve seat layout.'
    });
  }
}

module.exports = {
  searchBuses,
  getAllCities,
  getBusDetails,
  getScheduleSeats
};
