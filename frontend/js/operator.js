/**
 * BUSGO - Bus Operator Dashboard JS
 */

document.addEventListener('DOMContentLoaded', async () => {
  const user = getUser();
  if (!isLoggedIn() || (user?.role !== 'operator' && user?.role !== 'admin')) {
    showToast('Unauthorized access. Operator credentials required.', 'error');
    setTimeout(() => window.location.href = 'login.html', 1000);
    return;
  }

  // Load Initial Overview
  await loadDashboardOverview();
  await loadBusesList();
  await loadRoutesForSchedules();

  // Tab switching
  const navLinks = document.querySelectorAll('.sidebar-link[data-tab]');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const tabId = link.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      document.getElementById(tabId)?.classList.add('active');

      if (tabId === 'tabBuses') loadBusesList();
      if (tabId === 'tabBookings') loadOperatorBookings();
      if (tabId === 'tabRoutes') loadOperatorRoutes();
    });
  });

  // Add Bus Form
  const addBusForm = document.getElementById('addBusForm');
  if (addBusForm) {
    addBusForm.addEventListener('submit', handleAddBus);
  }

  // Add Schedule Form
  const addScheduleForm = document.getElementById('addScheduleForm');
  if (addScheduleForm) {
    addScheduleForm.addEventListener('submit', handleAddSchedule);
  }

  // Add Route Form
  const addRouteForm = document.getElementById('addRouteForm');
  if (addRouteForm) {
    addRouteForm.addEventListener('submit', handleAddRoute);
  }
});

async function loadDashboardOverview() {
  try {
    const res = await authFetch(`${API_BASE}/operator/dashboard`);
    const data = await res.json();

    if (res.ok && data.success) {
      document.getElementById('opTotalBuses').innerText = data.stats.totalBuses;
      document.getElementById('opTotalBookings').innerText = data.stats.totalBookings;
      document.getElementById('opTotalRevenue').innerText = formatCurrency(data.stats.totalRevenue);
      document.getElementById('opUpcomingTrips').innerText = data.stats.upcomingTrips;

      // Render recent bookings
      const container = document.getElementById('opRecentBookingsBody');
      if (container && data.recentBookings) {
        if (data.recentBookings.length === 0) {
          container.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px; color:#64748b;">No bookings recorded yet.</td></tr>`;
        } else {
          container.innerHTML = data.recentBookings.map(b => `
            <tr>
              <td><strong>${b.pnr_number}</strong></td>
              <td>${b.customer_name} (${b.customer_phone})</td>
              <td>${b.bus_name}</td>
              <td>${b.source_city} &rarr; ${b.destination_city}</td>
              <td>${formatDate(b.journey_date)}</td>
              <td><strong style="color:var(--primary);">${formatCurrency(b.total_amount)}</strong></td>
            </tr>
          `).join('');
        }
      }
    }
  } catch (err) {
    console.error('Operator dashboard error:', err);
  }
}

async function loadBusesList() {
  const container = document.getElementById('opBusesTableBody');
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/operator/buses`);
    const data = await res.json();

    if (res.ok && data.success) {
      const busSelect = document.getElementById('scheduleBusSelect');
      if (busSelect) {
        busSelect.innerHTML = `<option value="">Select a Bus</option>` + 
          data.buses.map(b => `<option value="${b.bus_id}">${b.bus_name} (${b.bus_number}) - ${b.bus_type}</option>`).join('');
      }

      if (data.buses.length === 0) {
        container.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px;">No buses registered yet. Click "Add New Bus" to get started!</td></tr>`;
      } else {
        container.innerHTML = data.buses.map(b => `
          <tr>
            <td><strong>${b.bus_name}</strong></td>
            <td><code>${b.bus_number}</code></td>
            <td><span class="badge badge-info">${b.bus_type.replace(/_/g, ' ')}</span></td>
            <td>${b.total_seats} Seats</td>
            <td>★ ${b.rating || '4.0'}</td>
            <td><span class="badge ${b.is_active ? 'badge-success' : 'badge-danger'}">${b.is_active ? 'Active' : 'Inactive'}</span></td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Load buses error:', err);
  }
}

async function handleAddBus(e) {
  e.preventDefault();
  const busName = document.getElementById('busName').value.trim();
  const busNumber = document.getElementById('busNumber').value.trim();
  const busType = document.getElementById('busType').value;
  const totalSeats = document.getElementById('totalSeats').value;
  const amenities = document.getElementById('amenities').value;

  try {
    const res = await authFetch(`${API_BASE}/operator/buses`, {
      method: 'POST',
      body: JSON.stringify({ busName, busNumber, busType, totalSeats, amenities })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      showToast('Bus and seat layout successfully created!', 'success');
      e.target.reset();
      closeModal('addBusModal');
      await loadBusesList();
      await loadDashboardOverview();
    } else {
      showToast(data.message || 'Failed to add bus.', 'error');
    }
  } catch (err) {
    showToast('Error registering bus.', 'error');
  }
}

async function loadRoutesForSchedules() {
  try {
    const res = await authFetch(`${API_BASE}/operator/routes`);
    const data = await res.json();
    if (res.ok && data.success) {
      const select = document.getElementById('scheduleRouteSelect');
      if (select) {
        select.innerHTML = `<option value="">Select a Route</option>` + 
          data.routes.map(r => `<option value="${r.route_id}">${r.source_city} &rarr; ${r.destination_city} (${r.distance_km} km)</option>`).join('');
      }

      const tableBody = document.getElementById('opRoutesTableBody');
      if (tableBody) {
        tableBody.innerHTML = data.routes.map(r => `
          <tr>
            <td><strong>${r.source_city}</strong></td>
            <td><strong>${r.destination_city}</strong></td>
            <td>${r.distance_km} km</td>
            <td>${Math.floor(r.duration_minutes / 60)}h ${r.duration_minutes % 60}m</td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Error loading routes:', err);
  }
}

async function handleAddSchedule(e) {
  e.preventDefault();
  const busId = document.getElementById('scheduleBusSelect').value;
  const routeId = document.getElementById('scheduleRouteSelect').value;
  const journeyDate = document.getElementById('scheduleDate').value;
  const departureTime = document.getElementById('scheduleDepTime').value;
  const arrivalTime = document.getElementById('scheduleArrTime').value;
  const ticketPrice = document.getElementById('schedulePrice').value;

  try {
    const res = await authFetch(`${API_BASE}/operator/schedules`, {
      method: 'POST',
      body: JSON.stringify({ busId, routeId, journeyDate, departureTime, arrivalTime, ticketPrice })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      showToast('Bus journey schedule published with real-time seat availability!', 'success');
      e.target.reset();
      closeModal('addScheduleModal');
      await loadDashboardOverview();
    } else {
      showToast(data.message || 'Failed to add schedule.', 'error');
    }
  } catch (err) {
    showToast('Error scheduling bus trip.', 'error');
  }
}

async function handleAddRoute(e) {
  e.preventDefault();
  const sourceCity = document.getElementById('routeSource').value.trim();
  const destinationCity = document.getElementById('routeDest').value.trim();
  const distanceKm = document.getElementById('routeDistance').value;
  const durationMinutes = document.getElementById('routeDuration').value;

  try {
    const res = await authFetch(`${API_BASE}/operator/routes`, {
      method: 'POST',
      body: JSON.stringify({ sourceCity, destinationCity, distanceKm, durationMinutes })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      showToast('Route added successfully!', 'success');
      e.target.reset();
      closeModal('addRouteModal');
      await loadRoutesForSchedules();
    } else {
      showToast(data.message || 'Failed to add route.', 'error');
    }
  } catch (err) {
    showToast('Error adding route.', 'error');
  }
}

async function loadOperatorBookings() {
  const container = document.getElementById('opBookingsTableBody');
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/operator/bookings`);
    const data = await res.json();

    if (res.ok && data.success) {
      if (data.bookings.length === 0) {
        container.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px;">No bookings found for your fleet yet.</td></tr>`;
      } else {
        container.innerHTML = data.bookings.map(b => `
          <tr>
            <td><strong>${b.pnr_number}</strong></td>
            <td>${b.customer_name}<br><small style="color:#64748b">${b.customer_phone}</small></td>
            <td>${b.bus_name}</td>
            <td>${b.source_city} &rarr; ${b.destination_city}</td>
            <td>${formatDate(b.journey_date)}</td>
            <td><span style="color:var(--primary); font-weight:700;">${b.seats_booked || 'N/A'}</span></td>
            <td><strong>${formatCurrency(b.total_amount)}</strong></td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Error loading operator bookings:', err);
  }
}

// Modal Helpers
function openModal(modalId) {
  document.getElementById(modalId)?.classList.add('active');
}
function closeModal(modalId) {
  document.getElementById(modalId)?.classList.remove('active');
}
