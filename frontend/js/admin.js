/**
 * BUSGO - Administrator Dashboard JS
 */

document.addEventListener('DOMContentLoaded', async () => {
  const user = getUser();
  if (!isLoggedIn() || user?.role !== 'admin') {
    showToast('Admin privilege required.', 'error');
    setTimeout(() => window.location.href = 'login.html', 1000);
    return;
  }

  // Load Overview
  await loadAdminOverview();

  // Tab switching
  const navLinks = document.querySelectorAll('.sidebar-link[data-tab]');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const tabId = link.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      document.getElementById(tabId)?.classList.add('active');

      if (tabId === 'tabAdminUsers') loadAdminUsers();
      if (tabId === 'tabAdminOperators') loadAdminOperators();
      if (tabId === 'tabAdminBookings') loadAdminBookings();
      if (tabId === 'tabAdminBuses') loadAdminBuses();
    });
  });
});

async function loadAdminOverview() {
  try {
    const res = await authFetch(`${API_BASE}/admin/dashboard`);
    const data = await res.json();

    if (res.ok && data.success) {
      document.getElementById('adminTotalCustomers').innerText = data.stats.totalCustomers;
      document.getElementById('adminTotalOperators').innerText = data.stats.totalOperators;
      document.getElementById('adminTotalBuses').innerText = data.stats.totalBuses;
      document.getElementById('adminTotalBookings').innerText = data.stats.totalBookings;
      document.getElementById('adminTotalRevenue').innerText = formatCurrency(data.stats.totalRevenue);
      document.getElementById('adminCancelledTickets').innerText = data.stats.cancelledBookings;

      // Recent Bookings
      const recentTable = document.getElementById('adminRecentBookingsBody');
      if (recentTable && data.recentBookings) {
        recentTable.innerHTML = data.recentBookings.map(b => `
          <tr>
            <td><strong>${b.pnr_number}</strong></td>
            <td>${b.customer_name}<br><small style="color:#64748b">${b.customer_email}</small></td>
            <td>${b.source_city} &rarr; ${b.destination_city}</td>
            <td>${b.bus_name}</td>
            <td><strong style="color:var(--primary);">${formatCurrency(b.total_amount)}</strong></td>
            <td><span class="badge ${b.booking_status === 'confirmed' ? 'badge-success' : 'badge-danger'}">${b.booking_status.toUpperCase()}</span></td>
          </tr>
        `).join('');
      }

      // Popular Routes
      const popTable = document.getElementById('adminPopularRoutesBody');
      if (popTable && data.popularRoutes) {
        popTable.innerHTML = data.popularRoutes.map(r => `
          <tr>
            <td><strong>${r.source_city} &rarr; ${r.destination_city}</strong></td>
            <td><strong>${r.booking_count}</strong> bookings</td>
            <td><strong style="color:var(--primary);">${formatCurrency(r.total_revenue)}</strong></td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Admin overview error:', err);
  }
}

async function loadAdminUsers() {
  const container = document.getElementById('adminUsersTableBody');
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/admin/users`);
    const data = await res.json();

    if (res.ok && data.success) {
      container.innerHTML = data.users.map(u => `
        <tr>
          <td>#${u.user_id}</td>
          <td><strong>${u.name}</strong></td>
          <td>${u.email}</td>
          <td>${u.phone}</td>
          <td><span class="badge badge-info">${u.role.toUpperCase()}</span></td>
          <td><span class="badge ${u.is_active ? 'badge-success' : 'badge-danger'}">${u.is_active ? 'Active' : 'Blocked'}</span></td>
          <td>
            <button onclick="toggleUserStatus(${u.user_id}, ${u.is_active ? 0 : 1})" class="btn btn-sm ${u.is_active ? 'btn-outline-primary' : 'btn-success'}">
              ${u.is_active ? 'Block' : 'Unblock'}
            </button>
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading users:', err);
  }
}

async function toggleUserStatus(userId, newStatus) {
  try {
    const res = await authFetch(`${API_BASE}/admin/users/${userId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ isActive: newStatus === 1 })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(data.message, 'success');
      loadAdminUsers();
    }
  } catch (err) {
    showToast('Failed to update user status.', 'error');
  }
}

async function loadAdminOperators() {
  const container = document.getElementById('adminOperatorsTableBody');
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/admin/operators`);
    const data = await res.json();

    if (res.ok && data.success) {
      container.innerHTML = data.operators.map(o => `
        <tr>
          <td><strong>${o.company_name}</strong></td>
          <td>${o.email}<br><small style="color:#64748b">${o.phone}</small></td>
          <td><code>${o.license_number || 'N/A'}</code></td>
          <td>${o.bus_count || 0} Buses</td>
          <td><span class="badge ${o.status === 'approved' ? 'badge-success' : (o.status === 'pending' ? 'badge-warning' : 'badge-danger')}">${o.status.toUpperCase()}</span></td>
          <td>
            ${o.status !== 'approved' ? `
              <button onclick="updateOperatorStatus(${o.operator_id}, 'approved')" class="btn btn-success btn-sm">Approve</button>
            ` : `
              <button onclick="updateOperatorStatus(${o.operator_id}, 'suspended')" class="btn btn-outline-primary btn-sm" style="color:var(--danger); border-color:var(--danger)">Suspend</button>
            `}
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading operators:', err);
  }
}

async function updateOperatorStatus(opId, status) {
  try {
    const res = await authFetch(`${API_BASE}/admin/operators/${opId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(data.message, 'success');
      loadAdminOperators();
      loadAdminOverview();
    }
  } catch (err) {
    showToast('Error updating operator status.', 'error');
  }
}

async function loadAdminBookings() {
  const container = document.getElementById('adminBookingsTableBody');
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/admin/bookings`);
    const data = await res.json();

    if (res.ok && data.success) {
      container.innerHTML = data.bookings.map(b => `
        <tr>
          <td><strong>${b.pnr_number}</strong></td>
          <td>${b.customer_name}</td>
          <td>${b.source_city} &rarr; ${b.destination_city}</td>
          <td>${b.bus_name}</td>
          <td>${formatDate(b.journey_date)}</td>
          <td><strong>${formatCurrency(b.total_amount)}</strong></td>
          <td><span class="badge ${b.booking_status === 'confirmed' ? 'badge-success' : 'badge-danger'}">${b.booking_status.toUpperCase()}</span></td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading bookings:', err);
  }
}

async function loadAdminBuses() {
  const container = document.getElementById('adminBusesTableBody');
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/admin/buses`);
    const data = await res.json();

    if (res.ok && data.success) {
      container.innerHTML = data.buses.map(b => `
        <tr>
          <td><strong>${b.bus_name}</strong></td>
          <td><code>${b.bus_number}</code></td>
          <td>${b.operator_name}</td>
          <td><span class="badge badge-info">${b.bus_type.replace(/_/g, ' ')}</span></td>
          <td>${b.total_seats}</td>
          <td>★ ${b.rating || '4.0'}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading buses:', err);
  }
}
