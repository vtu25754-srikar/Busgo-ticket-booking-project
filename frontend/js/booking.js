/**
 * BUSGO - Passenger Details & Booking Creation JS
 */

let checkoutData = null;
let appliedDiscount = 0;
let appliedCouponCode = null;

document.addEventListener('DOMContentLoaded', () => {
  // Check auth
  if (!isLoggedIn()) {
    window.location.href = 'login.html?redirect=passenger.html';
    return;
  }

  // Load checkout session
  const sessionStr = sessionStorage.getItem('busgo_checkout');
  if (!sessionStr) {
    showToast('No active booking session found. Redirecting to search...', 'info');
    setTimeout(() => window.location.href = 'index.html', 1200);
    return;
  }

  checkoutData = JSON.parse(sessionStr);

  renderJourneyHeader();
  renderPassengerInputs();
  prefillContactInfo();
  updateLiveFareSummary();

  // Coupon form listener
  const couponBtn = document.getElementById('btnApplyCoupon');
  if (couponBtn) {
    couponBtn.addEventListener('click', applyCoupon);
  }

  // Passenger form submission
  const bookingForm = document.getElementById('passengerDetailsForm');
  if (bookingForm) {
    bookingForm.addEventListener('submit', handleBookingSubmit);
  }
});

function renderJourneyHeader() {
  const container = document.getElementById('passengerJourneyHeader');
  if (!container || !checkoutData) return;

  const { schedule, selectedSeats, boardingPoint, droppingPoint } = checkoutData;
  container.innerHTML = `
    <div style="background:#ffffff; border-radius:12px; padding:20px; border:1px solid #e2e8f0; margin-bottom:24px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <h3 style="font-size:18px; font-weight:700;">${schedule.bus_name} (${schedule.operator_name || ''})</h3>
          <p style="color:var(--text-muted); font-size:13px; margin:4px 0;">
            <strong>${schedule.source_city}</strong> &rarr; <strong>${schedule.destination_city}</strong> | 
            ${formatDate(schedule.journey_date)} at ${formatTime(schedule.departure_time)}
          </p>
          <div style="display:flex; gap:14px; font-size:12px; color:#334155; margin-top:6px;">
            <span>📍 <strong>Boarding:</strong> ${boardingPoint || 'Central Terminal'}</span>
            <span>📍 <strong>Dropping:</strong> ${droppingPoint || 'Main Station'}</span>
          </div>
        </div>
        <div>
          <span style="background:var(--primary-light); color:var(--primary); padding:6px 14px; border-radius:20px; font-weight:600; font-size:13px;">
            Seats: ${selectedSeats.map(s => s.seat_number).join(', ')}
          </span>
        </div>
      </div>
    </div>
  `;
}

function renderPassengerInputs() {
  const container = document.getElementById('passengersContainer');
  if (!container || !checkoutData) return;

  const seats = checkoutData.selectedSeats;

  container.innerHTML = seats.map((seat, index) => `
    <div class="passenger-card" style="background:#ffffff; border-radius:12px; padding:20px; border:1px solid #e2e8f0; margin-bottom:16px;">
      <h4 style="font-size:15px; font-weight:600; margin-bottom:14px; color:var(--text-dark);">
        Passenger ${index + 1} - Seat <span style="color:var(--primary); font-weight:700;">${seat.seat_number}</span>
      </h4>
      <div style="display:grid; grid-template-columns: 2fr 1fr 1fr; gap:16px;">
        <div class="form-group" style="margin-bottom:0;">
          <label class="form-label">Full Name *</label>
          <input type="text" class="form-control" name="pName_${index}" required placeholder="e.g. Ramesh Kumar">
        </div>
        <div class="form-group" style="margin-bottom:0;">
          <label class="form-label">Age *</label>
          <input type="number" class="form-control" name="pAge_${index}" required min="1" max="110" placeholder="e.g. 28">
        </div>
        <div class="form-group" style="margin-bottom:0;">
          <label class="form-label">Gender *</label>
          <select class="form-control" name="pGender_${index}" required>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
    </div>
  `).join('');
}

function prefillContactInfo() {
  const user = getUser();
  if (user) {
    const emailField = document.getElementById('contactEmail');
    const phoneField = document.getElementById('contactPhone');
    if (emailField && user.email) emailField.value = user.email;
    if (phoneField && user.phone) phoneField.value = user.phone;
  }
}

function updateLiveFareSummary() {
  const count = checkoutData.selectedSeats.length;
  const unitPrice = Number(checkoutData.schedule.ticket_price);
  const baseFare = count * unitPrice;
  const convenienceFee = 50;
  const taxes = Math.round(baseFare * 0.05 * 100) / 100;
  const grandTotal = Math.max(0, baseFare + convenienceFee + taxes - appliedDiscount);

  document.getElementById('summaryBaseFare').innerText = formatCurrency(baseFare);
  document.getElementById('summaryTaxes').innerText = formatCurrency(taxes);
  document.getElementById('summaryDiscount').innerText = `- ${formatCurrency(appliedDiscount)}`;
  document.getElementById('summaryGrandTotal').innerText = formatCurrency(grandTotal);
}

/**
 * Coupon application
 */
async function applyCoupon() {
  const codeInput = document.getElementById('couponCodeInput');
  const code = codeInput.value.trim();

  if (!code) {
    showToast('Please enter a coupon code.', 'error');
    return;
  }

  const baseFare = checkoutData.selectedSeats.length * Number(checkoutData.schedule.ticket_price);

  try {
    const res = await authFetch(`${API_BASE}/bookings/validate-coupon`, {
      method: 'POST',
      body: JSON.stringify({ code, amount: baseFare })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      appliedDiscount = data.discountAmount !== undefined ? data.discountAmount : (data.discount || 0);
      appliedCouponCode = data.couponCode || code;
      showToast(data.message || `Coupon "${code}" applied! You saved ₹${appliedDiscount}`, 'success');
      updateLiveFareSummary();
    } else {
      showToast(data.message || 'Invalid coupon code.', 'error');
    }
  } catch (err) {
    console.error('Coupon error:', err);
    showToast('Failed to apply coupon.', 'error');
  }
}

/**
 * Handle Booking Form Submission
 */
async function handleBookingSubmit(e) {
  e.preventDefault();

  const seats = checkoutData.selectedSeats;
  const passengers = [];

  for (let i = 0; i < seats.length; i++) {
    const name = document.querySelector(`input[name="pName_${i}"]`).value.trim();
    const age = document.querySelector(`input[name="pAge_${i}"]`).value.trim();
    const gender = document.querySelector(`select[name="pGender_${i}"]`).value;

    if (!name || !age) {
      showToast(`Please complete details for Passenger ${i + 1}.`, 'error');
      return;
    }

    passengers.push({
      name,
      age: parseInt(age, 10),
      gender,
      seatId: seats[i].seat_id,
      seatNumber: seats[i].seat_number
    });
  }

  const contactEmail = document.getElementById('contactEmail').value.trim();
  const contactPhone = document.getElementById('contactPhone').value.trim();

  if (!contactEmail || !contactPhone) {
    showToast('Please provide valid contact email and phone number.', 'error');
    return;
  }

  const submitBtn = document.getElementById('btnSubmitBooking');
  submitBtn.disabled = true;
  submitBtn.innerText = 'Creating Booking Order...';

  const payload = {
    scheduleId: checkoutData.schedule.schedule_id,
    passengers,
    boardingStopId: checkoutData.boardingStopId,
    droppingStopId: checkoutData.droppingStopId,
    boarding_point: checkoutData.boardingPoint,
    dropping_point: checkoutData.droppingPoint,
    contactEmail: contactEmail,
    contactPhone: contactPhone,
    couponCode: appliedCouponCode
  };

  try {
    const res = await authFetch(`${API_BASE}/bookings/create`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok && data.success) {
      // Store confirmed booking in session
      sessionStorage.setItem('busgo_last_booking', JSON.stringify(data.booking));
      showToast('Booking successfully created! Proceeding to Payment...', 'success');

      setTimeout(() => {
        window.location.href = `payment.html?bookingId=${data.booking.bookingId}`;
      }, 800);
    } else {
      showToast(data.message || 'Booking failed.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerText = 'Proceed to Payment';
    }
  } catch (err) {
    console.error('Booking submission error:', err);
    showToast('An error occurred during booking. Please try again.', 'error');
    submitBtn.disabled = false;
    submitBtn.innerText = 'Proceed to Payment';
  }
}
