/**
 * BUSGO - Interactive Seat Selection JS
 */

let scheduleData = null;
let allSeats = [];
let selectedSeats = [];
let activeDeck = 'lower';
let routeMap = null;
let pickupMarker = null;
let dropMarker = null;
let routeLine = null;
let stopsDataMap = {};

document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  const scheduleId = params.get('scheduleId');

  if (!scheduleId) {
    showToast('Invalid schedule selected. Redirecting...', 'error');
    setTimeout(() => window.location.href = 'index.html', 1000);
    return;
  }

  await loadSeatLayout(scheduleId);
});

/**
 * Fetch and render seat layout
 */
async function loadSeatLayout(scheduleId) {
  try {
    const res = await fetch(`${API_BASE}/buses/schedules/${scheduleId}/seats`);
    const data = await res.json();

    if (!data.success) {
      showToast('Could not load seat layout.', 'error');
      return;
    }

    scheduleData = data.schedule;
    allSeats = data.seats;

    // Render journey header info
    renderHeaderInfo(scheduleData);

    // Populate Boarding & Dropping points
    populateStopPoints(data.stops);

    // Handle Deck Tabs
    setupDeckTabs(data.decks);

    // Initial render of seats
    renderDeckSeats(activeDeck);

    // Update initial price summary
    updateSummary();

  } catch (err) {
    console.error('Error loading seats:', err);
    showToast('Failed to connect to seat reservation server.', 'error');
  }
}

function renderHeaderInfo(schedule) {
  const container = document.getElementById('seatBusHeader');
  if (container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
          <h2 style="font-size:20px; font-weight:700;">${schedule.bus_name} (${schedule.operator_name})</h2>
          <span style="font-size:13px; color:var(--text-muted);">
            ${schedule.source_city || schedule.source} &rarr; ${schedule.destination_city || schedule.destination} | 
            Date: <strong>${formatDate(schedule.journey_date)}</strong> | 
            Departure: <strong>${formatTime(schedule.departure_time)}</strong>
            ${schedule.arrival_time ? ` | Arrival: <strong>${formatTime(schedule.arrival_time)}</strong>${schedule.arrival_next_day ? ' <span style="font-size:10px; color:#d84e55; font-weight:700; background:#fee2e2; padding:1px 5px; border-radius:4px;">Next Day</span>' : ''}` : ''}
          </span>
        </div>
        <div style="text-align:right;">
          <div style="font-size:12px; color:var(--text-muted);">Base Fare per seat</div>
          <div style="font-size:22px; font-weight:700; color:var(--primary);">${formatCurrency(schedule.ticket_price)}</div>
        </div>
      </div>
    `;
  }
}

function setupDeckTabs(decks) {
  const deckTabsContainer = document.getElementById('deckTabsContainer');
  if (!deckTabsContainer) return;

  if (decks.hasUpperDeck) {
    deckTabsContainer.innerHTML = `
      <div class="deck-tabs">
        <button class="deck-tab-btn active" id="tabLowerDeck" onclick="switchDeck('lower')">Lower Deck</button>
        <button class="deck-tab-btn" id="tabUpperDeck" onclick="switchDeck('upper')">Upper Deck</button>
      </div>
    `;
  } else {
    deckTabsContainer.innerHTML = `<div style="font-size:14px; font-weight:600; margin-bottom:12px; color:var(--text-muted);">Seating Layout</div>`;
  }
}

function switchDeck(deck) {
  activeDeck = deck;
  document.getElementById('tabLowerDeck')?.classList.toggle('active', deck === 'lower');
  document.getElementById('tabUpperDeck')?.classList.toggle('active', deck === 'upper');
  renderDeckSeats(deck);
}

/**
 * Render seat boxes in 2+1 or 2+2 grid format
 */
function renderDeckSeats(deck) {
  const container = document.getElementById('seatGridContainer');
  if (!container) return;

  const currentDeckSeats = allSeats.filter(s => {
    if (deck === 'lower') return s.deck === 'lower' || s.deck === 'single';
    return s.deck === 'upper';
  });

  const isSleeper = currentDeckSeats.some(s => s.seat_type.includes('berth'));

  container.className = `seat-grid ${isSleeper ? 'sleeper-grid' : 'seater-grid'}`;

  container.innerHTML = currentDeckSeats.map(seat => {
    const isSelected = selectedSeats.some(s => s.seat_id === seat.seat_id);
    const isBooked = seat.status === 'booked';
    const isFemale = seat.is_female_only;

    let seatClasses = ['seat-box'];
    if (isSleeper) seatClasses.push('sleeper');
    if (isBooked) seatClasses.push('booked');
    else if (isSelected) seatClasses.push('selected');
    else if (isFemale) seatClasses.push('female-only');

    return `
      <div class="${seatClasses.join(' ')}" 
           onclick="handleSeatClick(${seat.seat_id})"
           title="Seat ${seat.seat_number} - ${isBooked ? 'Booked' : (isFemale ? 'Female Only' : 'Available')}">
        <span>${seat.seat_number}</span>
        <span style="font-size:9px; opacity:0.8;">${formatCurrency(scheduleData.ticket_price)}</span>
      </div>
    `;
  }).join('');
}

/**
 * Seat Click Handler
 */
function handleSeatClick(seatId) {
  const seat = allSeats.find(s => s.seat_id === seatId);
  if (!seat || seat.status === 'booked') return;

  const existingIndex = selectedSeats.findIndex(s => s.seat_id === seatId);

  if (existingIndex > -1) {
    // Deselect
    selectedSeats.splice(existingIndex, 1);
  } else {
    // Max 6 seats per booking
    if (selectedSeats.length >= 6) {
      showToast('You can select a maximum of 6 seats per transaction.', 'info');
      return;
    }
    selectedSeats.push(seat);
  }

  renderDeckSeats(activeDeck);
  updateSummary();
}

/**
 * Update Right Summary Box
 */
function updateSummary() {
  const seatsListEl = document.getElementById('selectedSeatsDisplay');
  const countEl = document.getElementById('seatCountDisplay');
  const baseFareEl = document.getElementById('baseFareDisplay');
  const taxEl = document.getElementById('taxesDisplay');
  const totalEl = document.getElementById('totalAmountDisplay');
  const continueBtn = document.getElementById('btnContinueToPassengers');

  const count = selectedSeats.length;
  const unitPrice = Number(scheduleData?.ticket_price || 0);
  const baseFare = count * unitPrice;
  const convenienceFee = count > 0 ? 50 : 0;
  const taxes = Math.round(baseFare * 0.05 * 100) / 100;
  const grandTotal = baseFare + convenienceFee + taxes;

  if (seatsListEl) {
    seatsListEl.innerText = count > 0 ? selectedSeats.map(s => s.seat_number).join(', ') : 'None selected';
  }
  if (countEl) countEl.innerText = count;
  if (baseFareEl) baseFareEl.innerText = formatCurrency(baseFare);
  if (taxEl) taxEl.innerText = formatCurrency(taxes);
  if (totalEl) totalEl.innerText = formatCurrency(grandTotal);

  if (continueBtn) {
    continueBtn.disabled = count === 0;
  }
}

function populateStopPoints(stops) {
  const boardingSelect = document.getElementById('boardingStopSelect');
  const droppingSelect = document.getElementById('droppingStopSelect');

  if (!stops || !Array.isArray(stops)) return;

  // Support both flat array (stop_type field) and structured {boarding:[], dropping:[]} formats
  let boardingStops, droppingStops;
  if (stops.boarding && stops.dropping) {
    boardingStops = stops.boarding;
    droppingStops = stops.dropping;
  } else {
    boardingStops = stops.filter(s => s.stop_type === 'boarding');
    droppingStops = stops.filter(s => s.stop_type === 'dropping');
  }

  if (boardingSelect && boardingStops.length > 0) {
    boardingSelect.innerHTML = boardingStops.map(s => `
      <option value="${s.stop_id}">${s.stop_name} ${s.landmark ? `(${s.landmark})` : ''} - ${s.time || ''}</option>
    `).join('');
  }

  if (droppingSelect && droppingStops.length > 0) {
    droppingSelect.innerHTML = droppingStops.map(s => `
      <option value="${s.stop_id}">${s.stop_name} ${s.landmark ? `(${s.landmark})` : ''} - ${s.time || ''}</option>
    `).join('');
  }

  // Initialize Route & Boarding/Dropping Point Interactive Map
  initRouteMap(boardingStops, droppingStops);
}

/**
 * Interactive Route & Stop Locations Map via Leaflet
 */
function initRouteMap(boardingStops, droppingStops) {
  const mapEl = document.getElementById('routeMap');
  if (!mapEl || typeof L === 'undefined') return;

  // Index stops by stop_id
  [...boardingStops, ...droppingStops].forEach(s => {
    stopsDataMap[s.stop_id] = s;
  });

  if (!routeMap) {
    try {
      routeMap = L.map('routeMap', {
        zoomControl: true,
        attributionControl: false
      }).setView([15.0, 78.5], 6);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18
      }).addTo(routeMap);
    } catch (e) {
      console.warn('Map initialization failed:', e);
      return;
    }
  }

  const bSelect = document.getElementById('boardingStopSelect');
  const dSelect = document.getElementById('droppingStopSelect');

  if (bSelect) {
    bSelect.removeEventListener('change', updateRouteMap);
    bSelect.addEventListener('change', updateRouteMap);
  }
  if (dSelect) {
    dSelect.removeEventListener('change', updateRouteMap);
    dSelect.addEventListener('change', updateRouteMap);
  }

  setTimeout(() => {
    routeMap.invalidateSize();
    updateRouteMap();
  }, 200);
}

function updateRouteMap() {
  if (!routeMap || typeof L === 'undefined') return;

  const bSelect = document.getElementById('boardingStopSelect');
  const dSelect = document.getElementById('droppingStopSelect');
  const bStopId = bSelect?.value;
  const dStopId = dSelect?.value;

  const bStop = stopsDataMap[bStopId];
  const dStop = stopsDataMap[dStopId];

  const mapBLabel = document.getElementById('mapBoardingLabel');
  const mapDLabel = document.getElementById('mapDroppingLabel');
  const badge = document.getElementById('routeDistanceBadge');

  if (bStop && mapBLabel) {
    mapBLabel.innerText = `${bStop.stop_name} (${bStop.time || ''})`;
  }
  if (dStop && mapDLabel) {
    mapDLabel.innerText = `${dStop.stop_name} (${dStop.time || ''})`;
  }

  if (pickupMarker) routeMap.removeLayer(pickupMarker);
  if (dropMarker) routeMap.removeLayer(dropMarker);
  if (routeLine) routeMap.removeLayer(routeLine);

  const bLat = bStop?.latitude || 17.3850;
  const bLng = bStop?.longitude || 78.4867;
  const dLat = dStop?.latitude || 12.9716;
  const dLng = dStop?.longitude || 77.5946;

  const greenIcon = L.divIcon({
    html: '<div style="background:#16a34a; color:#fff; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:bold; border:2px solid #fff; box-shadow:0 2px 4px rgba(0,0,0,0.3);">📍</div>',
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });

  const redIcon = L.divIcon({
    html: '<div style="background:#dc2626; color:#fff; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:bold; border:2px solid #fff; box-shadow:0 2px 4px rgba(0,0,0,0.3);">🏁</div>',
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });

  pickupMarker = L.marker([bLat, bLng], { icon: greenIcon })
    .addTo(routeMap)
    .bindPopup(`<b>Pickup:</b> ${bStop?.stop_name || 'Boarding'}<br><small>${bStop?.address || ''}</small>`);

  dropMarker = L.marker([dLat, dLng], { icon: redIcon })
    .addTo(routeMap)
    .bindPopup(`<b>Drop:</b> ${dStop?.stop_name || 'Dropping'}<br><small>${dStop?.address || ''}</small>`);

  routeLine = L.polyline([[bLat, bLng], [dLat, dLng]], {
    color: '#d84e55',
    weight: 4,
    opacity: 0.85,
    dashArray: '6, 8'
  }).addTo(routeMap);

  const distKm = Math.round(calculateDistance(bLat, bLng, dLat, dLng));
  if (badge) {
    badge.innerText = `~${distKm} km | Direct Route`;
  }

  const bounds = L.latLngBounds([[bLat, bLng], [dLat, dLng]]);
  routeMap.fitBounds(bounds, { padding: [35, 35] });
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

/**
 * Continue to Passenger details
 */
async function proceedToPassengers() {
  if (selectedSeats.length === 0) {
    showToast('Please select at least one seat to continue.', 'error');
    return;
  }

  // Check login
  if (!isLoggedIn()) {
    showToast('Please login to proceed with booking.', 'info');
    setTimeout(() => {
      window.location.href = `login.html?redirect=${encodeURIComponent(window.location.href)}`;
    }, 800);
    return;
  }

  const bSelect = document.getElementById('boardingStopSelect');
  const dSelect = document.getElementById('droppingStopSelect');
  const boardingStopId = bSelect?.value;
  const droppingStopId = dSelect?.value;
  const boardingPoint = bSelect?.selectedOptions[0]?.text || '';
  const droppingPoint = dSelect?.selectedOptions[0]?.text || '';

  const continueBtn = document.getElementById('btnContinueToPassengers');
  if (continueBtn) {
    continueBtn.disabled = true;
    continueBtn.innerText = 'Reserving seats...';
  }

  // Lock selected seats on backend
  try {
    const res = await authFetch(`${API_BASE}/bookings/lock-seats`, {
      method: 'POST',
      body: JSON.stringify({
        scheduleId: scheduleData.schedule_id,
        seatIds: selectedSeats.map(s => s.seat_number || s.seat_id)
      })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      // Store checkout context in sessionStorage
      const checkoutContext = {
        schedule: scheduleData,
        selectedSeats: selectedSeats,
        boardingStopId,
        droppingStopId,
        boardingPoint,
        droppingPoint,
        lockedUntil: data.lockedUntil
      };

      sessionStorage.setItem('busgo_checkout', JSON.stringify(checkoutContext));
      window.location.href = 'passenger.html';
    } else {
      showToast(data.message || 'Could not lock selected seats. They may have been booked by someone else.', 'error');
      // Refresh seat layout
      await loadSeatLayout(scheduleData.schedule_id);
    }
  } catch (err) {
    console.error('Lock seats error:', err);
    showToast('Failed to lock seats. Please try again.', 'error');
  } finally {
    if (continueBtn) {
      continueBtn.disabled = false;
      continueBtn.innerText = 'Proceed to Passenger Details';
    }
  }
}
