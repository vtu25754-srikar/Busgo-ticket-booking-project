/**
 * BUSGO - Bus Search & Listing JS
 */

let allBusesData = [];

document.addEventListener('DOMContentLoaded', async () => {
  // Populate City Selects/Datalists
  await loadAvailableCities();

  // If search form is on home page
  const homeSearchForm = document.getElementById('homeSearchForm');
  if (homeSearchForm) {
    initHomeSearchForm(homeSearchForm);
  }

  // If on search results page (search.html)
  const resultsContainer = document.getElementById('busResultsContainer');
  if (resultsContainer) {
    initSearchResultsPage();
  }
});

/**
 * Load available cities from backend
 */
async function loadAvailableCities() {
  try {
    const res = await fetch(`${API_BASE}/buses/cities`);
    const data = await res.json();
    if (data.success && data.cities) {
      const cityList = document.getElementById('cityList');
      if (cityList) {
        cityList.innerHTML = data.cities.map(c => `<option value="${c}">${c}</option>`).join('');
      }

      // Also populate selects if any
      const fromSelect = document.getElementById('fromCity');
      const toSelect = document.getElementById('toCity');
      if (fromSelect && fromSelect.tagName === 'SELECT') {
        const defaultOptions = data.cities.map(c => `<option value="${c}">${c}</option>`).join('');
        fromSelect.innerHTML = `<option value="">Select Origin City</option>` + defaultOptions;
        toSelect.innerHTML = `<option value="">Select Destination City</option>` + defaultOptions;
      }
    }
  } catch (err) {
    console.warn('[search.js] Could not load dynamic city list:', err);
  }
}

/**
 * Swap origin and destination fields
 */
function swapCities() {
  const fromInput = document.getElementById('fromCity');
  const toInput = document.getElementById('toCity');
  if (fromInput && toInput) {
    const temp = fromInput.value;
    fromInput.value = toInput.value;
    toInput.value = temp;
  }
}

/**
 * Home Search Form Submission
 */
function initHomeSearchForm(form) {
  // Set default minimum date as today
  const dateInput = document.getElementById('journeyDate');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    if (!dateInput.value) dateInput.value = today;
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const from = document.getElementById('fromCity').value.trim();
    const to = document.getElementById('toCity').value.trim();
    const date = document.getElementById('journeyDate').value;
    const passengers = document.getElementById('passengers')?.value || 1;

    if (!from || !to) {
      showToast('Please select both Origin and Destination cities.', 'error');
      return;
    }
    if (from.toLowerCase() === to.toLowerCase()) {
      showToast('Origin and Destination cannot be the same city.', 'error');
      return;
    }
    if (!date) {
      showToast('Please select a journey date.', 'error');
      return;
    }

    const query = new URLSearchParams({
      from,
      to,
      date,
      passengers
    }).toString();

    window.location.href = `search.html?${query}`;
  });
}

/**
 * Search Results Page Logic
 */
async function initSearchResultsPage() {
  const params = new URLSearchParams(window.location.search);
  const from = params.get('from') || 'Hyderabad';
  const to = params.get('to') || 'Bangalore';
  const date = params.get('date') || new Date().toISOString().split('T')[0];
  const passengers = params.get('passengers') || '1';

  // Update top summary bar
  const searchSummary = document.getElementById('searchSummary');
  if (searchSummary) {
    searchSummary.innerHTML = `
      <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
        <div>
          <h2 style="font-size:20px; font-weight:700;">${from} &rarr; ${to}</h2>
          <span style="font-size:13px; color:var(--text-muted);">
            Date: <strong>${formatDate(date)}</strong> | Passengers: <strong>${passengers}</strong>
          </span>
        </div>
        <button onclick="window.location.href='index.html'" class="btn btn-secondary btn-sm">Modify Search</button>
      </div>
    `;
  }

  // Pre-fill search inputs if on search page
  const fromField = document.getElementById('fromCity');
  const toField = document.getElementById('toCity');
  const dateField = document.getElementById('journeyDate');
  if (fromField) fromField.value = from;
  if (toField) toField.value = to;
  if (dateField) dateField.value = date;

  // Fetch buses
  const container = document.getElementById('busResultsContainer');
  container.innerHTML = `
    <div style="text-align:center; padding: 60px 20px;">
      <div style="font-size: 32px; margin-bottom: 12px;">🚌</div>
      <h3>Searching available buses...</h3>
      <p style="color:var(--text-muted); font-size:14px;">Fetching real-time routes, prices and live seat availability</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/buses/search?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&date=${encodeURIComponent(date)}&passengers=${passengers}`);
    const data = await res.json();

    if (data.success && data.buses && data.buses.length > 0) {
      allBusesData = data.buses;
      renderBusResults(allBusesData);
      populateOperatorFilter(allBusesData);
      initFilterListeners();
    } else {
      container.innerHTML = `
        <div style="text-align:center; padding: 80px 20px; background:#fff; border-radius:12px; border:1px solid #e2e8f0;">
          <div style="font-size: 40px; margin-bottom: 14px;">🚍</div>
          <h3>No Buses Found for this Route</h3>
          <p style="color:var(--text-muted); margin: 8px 0 20px;">
            We couldn't find any buses running from <strong>${from}</strong> to <strong>${to}</strong> on <strong>${formatDate(date)}</strong>.
          </p>
          <a href="index.html" class="btn btn-primary">Search Another Route</a>
        </div>
      `;
    }
  } catch (err) {
    console.error('Error fetching buses:', err);
    container.innerHTML = `
      <div style="text-align:center; padding: 50px; background:#fff; border-radius:12px;">
        <h3 style="color:var(--danger)">Error Loading Search Results</h3>
        <p style="color:var(--text-muted)">Please ensure the backend server is running and try again.</p>
      </div>
    `;
  }
}

/**
 * Render bus cards to the DOM
 */
function renderBusResults(buses) {
  const container = document.getElementById('busResultsContainer');
  const countBadge = document.getElementById('busCountBadge');
  if (countBadge) countBadge.innerText = `${buses.length} Buses Available`;

  if (buses.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding: 50px; background:#fff; border-radius:12px;">
        <h4>No buses match your selected filters.</h4>
        <button onclick="resetFilters()" class="btn btn-outline-primary btn-sm" style="margin-top:10px;">Clear Filters</button>
      </div>
    `;
    return;
  }

  container.innerHTML = buses.map(bus => {
    const timing = (typeof calculateArrivalTime === 'function')
      ? calculateArrivalTime(bus.departure_time, bus.duration_text || '8h 30m')
      : { formattedArrival: formatTime(bus.arrival_time), isNextDay: Boolean(bus.arrival_next_day) };

    const arrivalDisplay = bus.arrival_time ? formatTime(bus.arrival_time) : timing.formattedArrival;
    const isNextDay = (bus.arrival_next_day !== undefined && bus.arrival_next_day !== null)
      ? Boolean(bus.arrival_next_day)
      : timing.isNextDay;

    return `
    <div class="bus-item-card">
      <div class="bus-item-main">
        <div>
          <div class="bus-operator-name">${bus.operator_name || 'Bus Operator'}</div>
          <div class="bus-type-label">${bus.bus_name || ''} | ${(bus.bus_type || '').replace(/_/g, ' ')}</div>
          <div class="bus-rating-badge">★ ${(Number(bus.rating) || 4.2).toFixed(1)}</div>
        </div>

        <div class="time-slot">
          <div class="time-val">${formatTime(bus.departure_time)}</div>
          <div class="city-val">${bus.source_city || bus.source}</div>
        </div>

        <div class="time-slot">
          <div class="duration-val">${bus.duration_text || '8h 30m'}</div>
          <div style="font-size:11px; color:#94a3b8; margin-top:4px;">Direct</div>
        </div>

        <div class="time-slot">
          <div class="time-val" style="display:flex; align-items:center; gap:6px;">
            <span>${arrivalDisplay}</span>
            ${isNextDay ? '<span style="font-size:10px; color:#d84e55; font-weight:700; background:#fee2e2; border:1px solid #fca5a5; padding:1px 5px; border-radius:4px; text-transform:uppercase;">Next Day</span>' : ''}
          </div>
          <div class="city-val">${bus.destination_city || bus.destination}</div>
        </div>

        <div class="bus-price-box">
          <div class="bus-price-amount">${formatCurrency(bus.ticket_price || bus.price)}</div>
          <div class="bus-seats-left">${bus.available_seats} Seats Left</div>
          <button onclick="selectBus(${bus.schedule_id || bus.bus_id})" class="btn btn-primary btn-sm" style="margin-top:8px; width:100%;">
            View Seats
          </button>
        </div>
      </div>

      <div class="bus-item-footer">
        <div class="amenities-tags">
          ${(bus.amenities_list || ['Charging Point', 'Water Bottle', 'Blanket'])
            .slice(0, 4)
            .map(a => `<span class="amenity-pill">${a}</span>`)
            .join('')}
        </div>
        <div>
          <span style="cursor:pointer; color:var(--primary); font-weight:500;" onclick="showBusPolicies()">Cancellation Policy</span>
        </div>
      </div>
    </div>
  `;
  }).join('');
}

/**
 * Handle "View Seats" button
 */
function selectBus(scheduleId) {
  const bus = allBusesData.find(b => b.schedule_id === scheduleId);
  if (bus) {
    sessionStorage.setItem('busgo_selected_schedule', JSON.stringify(bus));
    window.location.href = `seats.html?scheduleId=${scheduleId}`;
  }
}

/**
 * Filter and Sort listeners
 */
function initFilterListeners() {
  const checkboxes = document.querySelectorAll('.filter-option input');
  checkboxes.forEach(cb => {
    cb.addEventListener('change', applyFilters);
  });

  const sortSelect = document.getElementById('sortBySelect');
  if (sortSelect) {
    sortSelect.addEventListener('change', applyFilters);
  }
}

function applyFilters() {
  let filtered = [...allBusesData];

  // Bus Type Filters
  const selectedTypes = Array.from(document.querySelectorAll('input[name="busType"]:checked')).map(cb => cb.value);
  if (selectedTypes.length > 0) {
    filtered = filtered.filter(b => {
      return selectedTypes.some(t => {
        if (t === 'AC') return b.bus_type.includes('AC');
        if (t === 'NON_AC') return !b.bus_type.includes('NON_AC') ? false : true;
        if (t === 'SLEEPER') return b.bus_type.includes('SLEEPER');
        if (t === 'SEATER') return b.bus_type.includes('SEATER');
        return true;
      });
    });
  }

  // Operator Filters
  const selectedOps = Array.from(document.querySelectorAll('input[name="operatorFilter"]:checked')).map(cb => cb.value);
  if (selectedOps.length > 0) {
    filtered = filtered.filter(b => selectedOps.includes(b.operator_name));
  }

  // Sort
  const sort = document.getElementById('sortBySelect')?.value || 'price_asc';
  if (sort === 'price_asc') {
    filtered.sort((a, b) => Number(a.ticket_price) - Number(b.ticket_price));
  } else if (sort === 'price_desc') {
    filtered.sort((a, b) => Number(b.ticket_price) - Number(a.ticket_price));
  } else if (sort === 'rating_desc') {
    filtered.sort((a, b) => Number(b.rating) - Number(a.rating));
  } else if (sort === 'departure_asc') {
    filtered.sort((a, b) => a.departure_time.localeCompare(b.departure_time));
  }

  renderBusResults(filtered);
}

function resetFilters() {
  document.querySelectorAll('.filter-option input').forEach(cb => cb.checked = false);
  renderBusResults(allBusesData);
}

function populateOperatorFilter(buses) {
  const opContainer = document.getElementById('operatorFilterContainer');
  if (!opContainer) return;

  const operators = Array.from(new Set(buses.map(b => b.operator_name)));
  opContainer.innerHTML = operators.map(op => `
    <label class="filter-option">
      <input type="checkbox" name="operatorFilter" value="${op}">
      <span>${op}</span>
    </label>
  `).join('');
}

function showBusPolicies() {
  alert("BUSGO Cancellation Policy:\n\n• More than 72 hours before departure: 90% Refund\n• 24 - 72 hours before departure: 50% Refund\n• Less than 24 hours: 0% Refund\n\nRefund is automatically credited to the original payment method.");
}
