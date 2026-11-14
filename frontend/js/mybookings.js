/**
 * BUSGO - My Bookings & Ticket Management JS
 */

let myBookingsData = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!isLoggedIn()) {
    window.location.href = 'login.html?redirect=mybookings.html';
    return;
  }

  await loadUserBookings();

  // Tab switching
  const tabButtons = document.querySelectorAll('.booking-tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tabName = btn.getAttribute('data-tab');
      renderBookingsTab(tabName);
    });
  });
});

/**
 * Fetch bookings
 */
async function loadUserBookings() {
  const container = document.getElementById('bookingsListContainer');
  container.innerHTML = `
    <div style="text-align:center; padding:50px;">
      <div style="font-size:28px;">⏳</div>
      <p style="color:var(--text-muted); margin-top:8px;">Loading your journeys...</p>
    </div>
  `;

  try {
    const res = await authFetch(`${API_BASE}/bookings/my-bookings`);
    const data = await res.json();

    if (res.ok && data.success) {
      myBookingsData = data.bookings;
      renderBookingsTab('upcoming');
    } else {
      container.innerHTML = `
        <div style="text-align:center; padding:40px; background:#fff; border-radius:12px;">
          <p style="color:var(--danger)">Failed to load bookings: ${data.message}</p>
        </div>
      `;
    }
  } catch (err) {
    console.error('Error fetching bookings:', err);
    container.innerHTML = `
      <div style="text-align:center; padding:40px; background:#fff; border-radius:12px;">
        <p style="color:var(--danger)">Network error while loading your bookings.</p>
      </div>
    `;
  }
}

/**
 * Render bookings list for selected tab
 */
function renderBookingsTab(tabName) {
  const container = document.getElementById('bookingsListContainer');
  if (!myBookingsData || !container) return;

  const bookings = myBookingsData[tabName] || [];

  if (bookings.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:60px 20px; background:#fff; border-radius:12px; border:1px solid #e2e8f0;">
        <div style="font-size:42px; margin-bottom:12px;">🎟️</div>
        <h3>No ${tabName} bookings found</h3>
        <p style="color:var(--text-muted); margin: 8px 0 20px;">You do not have any ${tabName} bus journeys right now.</p>
        <a href="index.html" class="btn btn-primary btn-sm">Book a Bus Ticket</a>
      </div>
    `;
    return;
  }

  container.innerHTML = bookings.map(b => {
    const isCancelled = b.booking_status === 'cancelled';
    const statusBadgeClass = isCancelled ? 'badge-danger' : (tabName === 'completed' ? 'badge-info' : 'badge-success');
    const statusText = isCancelled ? 'CANCELLED' : (tabName === 'completed' ? 'COMPLETED' : 'CONFIRMED');

    return `
      <div class="booking-card" style="background:#ffffff; border-radius:12px; border:1px solid #e2e8f0; padding:20px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; border-bottom:1px solid #f1f5f9; padding-bottom:14px; margin-bottom:14px;">
          <div>
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="font-size:16px; font-weight:700; color:var(--text-dark);">
                ${b.source_city} &rarr; ${b.destination_city}
              </span>
              <span class="badge ${statusBadgeClass}">${statusText}</span>
            </div>
            <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">
              PNR: <strong style="color:var(--primary);">${b.pnr_number}</strong> | Operator: <strong>${b.operator_name || b.bus_name}</strong>${b.bus_number ? ` | Bus No: <strong style="color:#b91c1c;">${b.bus_number}</strong>` : ''}
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:18px; font-weight:700; color:var(--primary);">${formatCurrency(b.total_amount)}</div>
            <div style="font-size:11px; color:#10b981; font-weight:600;">Payment: ${String(b.payment_status || 'Paid').toUpperCase()}</div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; font-size:13px; margin-bottom:16px;">
          <div>
            <span style="color:var(--text-muted);">Date & Time:</span><br>
            <strong>${formatDate(b.journey_date)}</strong> at <strong>${formatTime(b.departure_time)}</strong>
          </div>
          <div>
            <span style="color:var(--text-muted);">Bus Details:</span><br>
            <strong>${b.bus_name}</strong> (${b.bus_type.replace(/_/g, ' ')})
          </div>
          <div>
            <span style="color:var(--text-muted);">Seat(s):</span><br>
            <strong style="color:var(--primary); font-size:14px;">${b.seats_booked || b.seat_number || 'N/A'}</strong>
          </div>
          ${b.boarding_point ? `
          <div>
            <span style="color:var(--text-muted);">Boarding:</span><br>
            <span style="color:#334155; font-size:12px;">📍 ${b.boarding_point}</span>
          </div>
          ` : ''}
        </div>

        <div style="display:flex; justify-content:flex-end; gap:10px; border-top:1px solid #f1f5f9; padding-top:14px;">
          <button onclick="downloadTicketPdf(${b.booking_id}, '${b.pnr_number}')" class="btn btn-secondary btn-sm">
            📥 Print / View Ticket
          </button>
          ${!isCancelled && tabName === 'upcoming' ? `
            <button onclick="openCancelModal(${b.booking_id}, '${b.pnr_number}', ${b.total_amount})" class="btn btn-outline-primary btn-sm" style="border-color:#ef4444; color:#ef4444;">
              Cancel Ticket
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Download Ticket PDF
 */
async function downloadTicketPdf(bookingId, pnr) {
  try {
    showToast('Opening print-ready electronic ticket...', 'info');
    const ticketUrl = `${API_BASE}/bookings/${bookingId}/download-ticket`;
    window.open(ticketUrl, '_blank', 'width=800,height=900,scrollbars=yes');
  } catch (err) {
    console.error('Download ticket error:', err);
    showToast('Failed to open ticket.', 'error');
  }
}

/**
 * Open Cancellation Modal
 */
let cancelBookingId = null;

function openCancelModal(bookingId, pnr, amount) {
  cancelBookingId = bookingId;
  const modal = document.getElementById('cancelBookingModal');
  if (modal) {
    document.getElementById('cancelPnrDisplay').innerText = pnr;
    document.getElementById('cancelAmountDisplay').innerText = formatCurrency(amount);
    modal.classList.add('active');
  }
}

function closeCancelModal() {
  cancelBookingId = null;
  const modal = document.getElementById('cancelBookingModal');
  if (modal) modal.classList.remove('active');
}

async function confirmCancellation() {
  if (!cancelBookingId) return;

  const reason = document.getElementById('cancelReasonSelect')?.value || 'Change in travel plans';
  const confirmBtn = document.getElementById('btnConfirmCancel');
  confirmBtn.disabled = true;
  confirmBtn.innerText = 'Cancelling...';

  try {
    const res = await authFetch(`${API_BASE}/bookings/cancel/${cancelBookingId}`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast(`Booking cancelled. Refund of ₹${data.refund.refundAmount} initiated!`, 'success');
      closeCancelModal();
      await loadUserBookings();
    } else {
      showToast(data.message || 'Failed to cancel booking.', 'error');
    }
  } catch (err) {
    console.error('Cancel booking error:', err);
    showToast('Network error during cancellation.', 'error');
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.innerText = 'Confirm Cancellation';
  }
}
