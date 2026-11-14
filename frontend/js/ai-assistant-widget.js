/**
 * BUSGO - AI Travel Assistant Widget (Claude AI & RAG Tool Calling)
 * Injects conversational AI drawer and floating trigger button across all pages.
 */

(function () {
  document.addEventListener('DOMContentLoaded', () => {
    initAiWidget();
  });

  function initAiWidget() {
    // 1. Inject Stylesheet if not present
    if (!document.getElementById('aiAssistantCss')) {
      const link = document.createElement('link');
      link.id = 'aiAssistantCss';
      link.rel = 'stylesheet';
      link.href = 'css/ai-assistant.css';
      document.head.appendChild(link);
    }

    // 2. Inject Floating Button
    const floatBtn = document.createElement('button');
    floatBtn.className = 'ai-floating-btn';
    floatBtn.id = 'aiFloatingBtn';
    floatBtn.innerHTML = `
      <div class="ai-btn-pulse"></div>
      <span style="font-size:20px;">🤖</span>
      <span>AI Travel Assistant</span>
    `;
    floatBtn.onclick = toggleAiDrawer;
    document.body.appendChild(floatBtn);

    // 3. Inject Drawer & Overlay
    const overlay = document.createElement('div');
    overlay.className = 'ai-drawer-overlay';
    overlay.id = 'aiDrawerOverlay';
    overlay.onclick = toggleAiDrawer;
    document.body.appendChild(overlay);

    const drawer = document.createElement('div');
    drawer.className = 'ai-drawer';
    drawer.id = 'aiDrawer';
    drawer.innerHTML = `
      <div class="ai-header">
        <div class="ai-header-title">
          <span style="font-size:22px;">🤖</span>
          <div>
            <div style="font-weight:700; font-size:15px;">BUSGO AI Assistant</div>
            <div style="font-size:11px; opacity:0.8;">Powered by Claude & RAG Knowledge Base</div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="ai-badge">Agentic AI</span>
          <button class="ai-close-btn" onclick="window.toggleAiDrawer()">&times;</button>
        </div>
      </div>

      <div class="ai-quick-chips">
        <div class="ai-chip" onclick="window.sendQuickPrompt('Find a sleeper bus from Hyderabad to Bangalore under 1000 rupees')">
          🚍 Sleeper under ₹1000
        </div>
        <div class="ai-chip" onclick="window.sendQuickPrompt('Compare cheapest sleeper buses from Hyderabad to Bangalore')">
          ⚖️ Compare Options
        </div>
        <div class="ai-chip" onclick="window.sendQuickPrompt('What is the refund percentage if I cancel 30 hours before travel?')">
          📄 Refund Policy (RAG)
        </div>
        <div class="ai-chip" onclick="window.sendQuickPrompt('What is the luggage weight allowance?')">
          🧳 Luggage Rules
        </div>
        <div class="ai-chip" onclick="window.sendQuickPrompt('Show my booking history')">
          🎟️ My Bookings
        </div>
      </div>

      <div class="ai-messages" id="aiMessagesContainer">
        <div class="ai-msg assistant">
          👋 <strong>Hello! I am your Intelligent BUSGO Travel Assistant.</strong><br><br>
          You can ask me in plain English to search buses, compare prices, check seat availability, explain cancellation rules, or review luggage guidelines!
        </div>
      </div>

      <form class="ai-input-bar" id="aiChatForm">
        <input type="text" class="ai-input" id="aiChatInput" placeholder="Ask e.g. 'Find sleeper bus to Bangalore tomorrow'..." autocomplete="off" />
        <button type="submit" class="ai-send-btn">Send</button>
      </form>
    `;
    document.body.appendChild(drawer);

    // Form Listener
    document.getElementById('aiChatForm').addEventListener('submit', (e) => {
      e.preventDefault();
      const input = document.getElementById('aiChatInput');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      sendAiMessage(msg);
    });
  }

  // Global toggle function
  window.toggleAiDrawer = function () {
    const drawer = document.getElementById('aiDrawer');
    const overlay = document.getElementById('aiDrawerOverlay');
    if (!drawer || !overlay) return;

    const isActive = drawer.classList.contains('active');
    if (isActive) {
      drawer.classList.remove('active');
      overlay.classList.remove('active');
    } else {
      drawer.classList.add('active');
      overlay.classList.add('active');
      document.getElementById('aiChatInput')?.focus();
    }
  };

  window.sendQuickPrompt = function (text) {
    sendAiMessage(text);
  };

  async function sendAiMessage(message, payloadObj = null) {
    const container = document.getElementById('aiMessagesContainer');
    if (!container) return;

    // Append User Message
    const userBubble = document.createElement('div');
    userBubble.className = 'ai-msg user';
    userBubble.innerText = message;
    container.appendChild(userBubble);
    container.scrollTop = container.scrollHeight;

    // Append Thinking placeholder
    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'ai-msg assistant';
    loadingBubble.id = 'aiLoadingBubble';
    loadingBubble.innerHTML = `<span style="font-size:12px; color:#64748b;">⏳ Thinking & selecting approved tools...</span>`;
    container.appendChild(loadingBubble);
    container.scrollTop = container.scrollHeight;

    try {
      const user = (typeof getUser === 'function') ? getUser() : null;
      const userId = user ? user.user_id : 1;

      const API_ENDPOINT = (typeof API_BASE !== 'undefined') ? `${API_BASE}/chat` : '/api/chat';

      const bodyData = Object.assign({ message, user_id: userId }, payloadObj || {});

      const res = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
      });

      const data = await res.json();
      loadingBubble.remove();

      renderAgentResponse(data, container);

      // If booking was created, automatically redirect directly to Payment Gateway
      if (data && data.type === 'ticket_booked' && data.booking) {
        try {
          sessionStorage.setItem('busgo_last_booking', JSON.stringify(data.booking));
        } catch (e) {}

        const payUrl = data.booking.payment_url || (`payment.html?bookingId=${data.booking.booking_id}`);

        const autoNotice = document.createElement('div');
        autoNotice.style.cssText = 'background:#ecfdf5; border:1px solid #10b981; border-radius:8px; padding:10px; margin-top:8px; font-size:12px; color:#065f46; font-weight:600; text-align:center; animation:fadeIn 0.2s ease-in;';
        autoNotice.innerHTML = '🚀 <strong>Seats Reserved!</strong> Proceeding directly to Payment Checkout in 1s...';
        container.appendChild(autoNotice);
        container.scrollTop = container.scrollHeight;

        setTimeout(() => {
          window.location.href = payUrl;
        }, 1100);
      }

    } catch (err) {
      console.error('[AI Assistant Error]:', err);
      loadingBubble.innerHTML = `<span style="color:#ef4444;">Could not connect to AI Assistant backend server. Please verify Flask backend is active on port 5000.</span>`;
    }
    container.scrollTop = container.scrollHeight;
  }

  function renderAgentResponse(data, container) {
    const bubble = document.createElement('div');
    bubble.className = 'ai-msg assistant';

    let toolHtml = '';
    if (data.tool_called) {
      toolHtml = `
        <div class="ai-tool-pill">
          <span>⚡ Approved Tool Executed:</span>
          <code>${data.tool_called}()</code>
        </div>
      `;
    }

    // Markdown conversion for bold and linebreaks
    let replyText = (data.reply || '')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    // Optional RAG source badge
    let sourcesHtml = '';
    if (data.sources && data.sources.length > 0) {
      sourcesHtml = `
        <div style="margin-top:10px; font-size:11px; color:#059669; background:#ecfdf5; border:1px solid #a7f3d0; border-radius:6px; padding:4px 8px;">
          📚 Grounded in Knowledge Base: <strong>${data.sources.join(', ')}</strong>
        </div>
      `;
    }

    // Render booking card – payment pending (user must pay to confirm)
    let bookedCardHtml = '';
    if (data.type === 'ticket_booked' && data.booking) {
      const b = data.booking;
      const payUrl = b.payment_url || `/payment.html?bookingId=${b.booking_id}`;
      const genderStr = b.passenger_gender ? `${b.passenger_gender}, ` : '';
      const hasDiscount = b.discount && Number(b.discount) > 0;
      const discountSnippet = hasDiscount
        ? `<div style="color:#16a34a; font-weight:700; margin:3px 0;">🏷️ Coupon Applied: <strong>${b.coupon_code}</strong> (Saved ₹${Number(b.discount).toFixed(2)})</div>
           <div>💰 Total to Pay: <span style="text-decoration:line-through; color:#94a3b8; font-size:12px;">₹${Number(b.original_fare || (Number(b.fare) + Number(b.discount))).toFixed(2)}</span> <strong style="color:#b91c1c; font-size:14px;">₹${Number(b.fare).toFixed(2)}</strong></div>`
        : `<div>💰 Total Fare: <strong>₹${Number(b.fare).toFixed(2)}</strong></div>`;

      bookedCardHtml = `
        <div class="ai-booking-confirm-card" style="background:#fffbeb; border:1px solid #fbbf24; border-radius:10px; padding:14px; margin-top:10px; font-size:13px;">
          <div style="font-weight:700; color:#92400e; margin-bottom:8px; font-size:14px;">🔒 Booking Reserved — Payment Pending</div>
          <div>🎫 PNR: <strong>${b.pnr}</strong></div>
          <div>👤 Passenger: <strong>${b.passenger_name}</strong> (${genderStr}${b.passenger_age} yrs)</div>
          <div>🚍 ${b.bus_operator} (${b.bus_type})</div>
          <div>📍 Boarding: ${b.boarding_point}</div>
          <div>🏁 Dropping: ${b.dropping_point}</div>
          <div>💺 Seat: <strong>${b.seat_number}</strong></div>
          ${discountSnippet}
          <div style="margin-top:6px; font-size:12px; color:#b45309;">⏰ Complete payment within 10 minutes to confirm and print your ticket.</div>
          <div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">
            <a href="${payUrl}" class="btn btn-primary btn-sm" style="font-size:12px; text-decoration:none; background:#16a34a; color:#fff; padding:6px 16px; border-radius:6px; font-weight:600;">💳 Proceed to Payment →</a>
            <a href="mybookings.html" class="btn btn-secondary btn-sm" style="font-size:11px; text-decoration:none;">View My Bookings</a>
          </div>
        </div>
      `;
    }

    // Render interactive in-chat Form if passenger details / form needed
    let formHtml = '';
    const formId = 'pform_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
    if (data.type === 'passenger_form_needed' || data.type === 'passenger_details_needed') {
      const bps = data.available_boarding_points || [];
      const dps = data.available_dropping_points || [];
      const availSeats = data.available_seats || [];
      const decks = data.decks || {};
      const applicableCoupons = data.applicable_coupons || [
        { code: 'SUMMER20', title: '20% OFF', badge: 'HOLIDAY', savings_text: 'Save 20%' },
        { code: 'FIRST10', title: '10% OFF', badge: 'POPULAR', savings_text: 'Save 10%' },
        { code: 'SAVE100', title: '₹100 FLAT', badge: 'BEST VALUE', savings_text: 'Save ₹100' },
        { code: 'BUSGO50', title: '₹50 FLAT', badge: 'INSTANT', savings_text: 'Save ₹50' }
      ];

      const availableBuses = data.available_buses || [];
      const hasMultipleBuses = availableBuses.length > 1;

      let busSelectionSectionHtml = '';
      if (availableBuses.length > 0) {
        busSelectionSectionHtml = `
          <!-- Comfort Price & Bus Selection Section -->
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px; margin-bottom:12px;">
            <!-- Comfort Price Dropdown -->
            <div style="margin-bottom:8px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <label style="font-weight:700; font-size:12px; color:#1e293b;">💰 Select Comfort Price (Budget):</label>
                <span id="aiPriceMatchCount_${formId}" style="font-size:11px; font-weight:700; color:#16a34a;">${availableBuses.length} buses available</span>
              </div>
              <select id="aiPriceFilter_${formId}" class="form-control" style="width:100%; height:34px; border:1.5px solid #cbd5e1; border-radius:6px; padding:2px 8px; font-size:12px; background:#ffffff; font-weight:600; color:#0f172a;">
                <option value="all">🌟 All Comfort Prices (Any Budget)</option>
                <option value="600">Economy: Up to ₹600</option>
                <option value="800">Standard: Up to ₹800</option>
                <option value="1000">Comfort: Up to ₹1,000</option>
                <option value="1200">Premium: Up to ₹1,200</option>
                <option value="1500">Luxury: Up to ₹1,500</option>
              </select>
            </div>

            <!-- Bus Dropdown Area (Shows if 2 or more buses match specification) -->
            <div id="aiBusDropdownArea_${formId}" style="${hasMultipleBuses ? 'display:block;' : 'display:none;'} margin-bottom:8px;">
              <label style="font-weight:700; font-size:11px; color:#334155; display:block; margin-bottom:3px;">
                🚍 Select Your Preferred Bus:
              </label>
              <select id="aiBusSelect_${formId}" class="form-control" style="width:100%; height:34px; border:1.5px solid #cbd5e1; border-radius:6px; padding:2px 8px; font-size:12px; background:#ffffff; font-weight:600; color:#0f172a;">
                ${availableBuses.map(b => `
                  <option value="${b.bus_id}" data-price="${b.price}" data-bus-number="${b.bus_number}" data-operator="${b.operator_name}" data-type="${b.bus_type}" ${b.bus_id == data.bus_id ? 'selected' : ''}>
                    ${b.operator_name} (${b.bus_type}) | ₹${b.price.toFixed(2)} | Bus #${b.bus_number}
                  </option>
                `).join('')}
              </select>
            </div>

            <!-- Active Selected Bus Badge -->
            <div id="aiChosenBusInfo_${formId}" style="font-size:11px; color:#334155; display:flex; justify-content:space-between; align-items:center; background:#ffffff; border:1px solid #bbf7d0; border-radius:6px; padding:6px 10px; background:#f0fdf4;">
              <span>🚍 <strong>${data.bus_operator}</strong> (${data.bus_type || ''})</span>
              <span style="color:#b91c1c; font-weight:800; background:#fee2e2; padding:2px 8px; border-radius:4px; font-size:12px;">Bus #${data.bus_number || ''}</span>
            </div>
          </div>
        `;
      } else {
        // Single bus option badge
        busSelectionSectionHtml = `
          <div style="background:#fef2f2; border:1px dashed #fca5a5; border-radius:8px; padding:8px 12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:700; font-size:12px; color:#991b1b;">🚍 ${data.bus_operator} (${data.bus_type || ''})</div>
              <small style="color:#64748b; font-size:11px;">Vehicle Number for boarding:</small>
            </div>
            <span style="font-weight:800; font-size:12px; color:#b91c1c; background:#fee2e2; padding:3px 8px; border-radius:6px;">
              Bus #${data.bus_number || ''}
            </span>
          </div>
        `;
      }

      formHtml = `
        <div class="ai-passenger-form" id="${formId}" style="background:#ffffff; border:1.5px solid #d84e55; border-radius:12px; padding:14px; margin-top:10px; font-size:13px; color:#0f172a; box-shadow: 0 4px 14px rgba(216,78,85,0.08);">
          <div style="font-weight:700; color:#b91c1c; margin-bottom:10px; font-size:14px; display:flex; justify-content:space-between; align-items:center;">
            <span>📝 Passenger & Comfort Seat Details</span>
            <span id="aiTopPriceBadge_${formId}" style="font-size:11px; font-weight:600; background:#fef2f2; color:#b91c1c; padding:2px 8px; border-radius:8px;">₹${Number(data.fare_per_seat || 0).toFixed(2)}/seat ${data.bus_number ? `| Bus #${data.bus_number}` : ''}</span>
          </div>

          ${busSelectionSectionHtml}

          <!-- Number of Passengers -->
          <div style="margin-bottom:10px;">
            <label style="font-weight:600; font-size:12px; color:#334155; display:block; margin-bottom:4px;">👥 Number of Passengers:</label>
            <select id="aiNumP_${formId}" class="form-control" style="width:100%; height:34px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 8px; font-size:13px; background:#f8fafc; font-weight:600;">
              <option value="1" selected>1 Passenger</option>
              <option value="2">2 Passengers</option>
              <option value="3">3 Passengers</option>
              <option value="4">4 Passengers</option>
              <option value="5">5 Passengers</option>
              <option value="6">6 Passengers</option>
            </select>
          </div>

          <!-- Passenger Fields List -->
          <div id="aiPList_${formId}" style="margin-bottom:8px;"></div>

          <!-- Interactive Seat Map Toggle Button -->
          <div style="margin-bottom:12px;">
            <button type="button" id="aiToggleSeatMap_${formId}" style="width:100%; padding:6px 10px; background:#f1f5f9; border:1px dashed #94a3b8; border-radius:6px; font-size:11px; font-weight:600; color:#334155; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px;">
              <span>💺 View Bus Seat Map & Pick Comfort Seats</span>
            </button>

            <!-- Collapsible Visual Seat Map -->
            <div id="aiSeatMapBox_${formId}" style="display:none; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-top:8px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; font-size:11px; color:#64748b;">
                <span>🟢 Available | 🔴 Booked | 🔵 Selected</span>
                <span style="font-size:10px;">(Click to assign seat)</span>
              </div>

              <!-- Lower Deck -->
              <div style="font-weight:700; font-size:11px; color:#475569; margin:4px 0 2px;">⬇️ Lower Deck</div>
              <div class="ai-lower-deck-grid" style="display:grid; grid-template-columns: repeat(6, 1fr); gap:4px; margin-bottom:8px;">
                ${(decks.lower || []).map(s => {
                  const isAvail = s.status === 'available';
                  return `<div class="ai-map-seat" data-seat="${s.seat_number}" style="height:24px; border-radius:4px; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center; cursor:${isAvail ? 'pointer' : 'not-allowed'}; background:${isAvail ? '#dcfce7' : '#e2e8f0'}; color:${isAvail ? '#166534' : '#94a3b8'}; border:1px solid ${isAvail ? '#86efac' : '#cbd5e1'}; user-select:none;">${s.seat_number}</div>`;
                }).join('')}
              </div>

              <!-- Upper Deck -->
              <div style="font-weight:700; font-size:11px; color:#475569; margin:4px 0 2px;">⬆️ Upper Deck (Sleepers)</div>
              <div class="ai-upper-deck-grid" style="display:grid; grid-template-columns: repeat(6, 1fr); gap:4px;">
                ${(decks.upper || []).map(s => {
                  const isAvail = s.status === 'available';
                  return `<div class="ai-map-seat" data-seat="${s.seat_number}" style="height:24px; border-radius:4px; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center; cursor:${isAvail ? 'pointer' : 'not-allowed'}; background:${isAvail ? '#dcfce7' : '#e2e8f0'}; color:${isAvail ? '#166534' : '#94a3b8'}; border:1px solid ${isAvail ? '#86efac' : '#cbd5e1'}; user-select:none;">${s.seat_number}</div>`;
                }).join('')}
              </div>
            </div>
          </div>

          <!-- Boarding Point Dropdown -->
          <div style="margin-bottom:10px;">
            <label style="font-weight:600; font-size:12px; color:#334155; display:block; margin-bottom:4px;">📍 Boarding Point (${data.source || 'Origin'}):</label>
            <select id="aiBp_${formId}" class="form-control" style="width:100%; height:34px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 8px; font-size:12px; background:#f8fafc;">
              ${bps.map(bp => `<option value="${bp}">${bp}</option>`).join('')}
            </select>
          </div>

          <!-- Dropping Point Dropdown -->
          <div style="margin-bottom:12px;">
            <label style="font-weight:600; font-size:12px; color:#334155; display:block; margin-bottom:4px;">🏁 Dropping Point (${data.destination || 'Destination'}):</label>
            <select id="aiDp_${formId}" class="form-control" style="width:100%; height:34px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 8px; font-size:12px; background:#f8fafc;">
              ${dps.map(dp => `<option value="${dp}">${dp}</option>`).join('')}
            </select>
          </div>

          <!-- Coupon & Promotional Discount Section -->
          <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:8px; padding:10px; margin-bottom:12px;">
            <div style="font-weight:700; font-size:12px; color:#166534; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
              <span>🏷️ Apply Coupon & Save</span>
              <span id="aiCouponTag_${formId}" style="display:none; font-size:10px; background:#dcfce7; color:#15803d; padding:2px 6px; border-radius:4px; font-weight:700; border:1px solid #86efac;"></span>
            </div>

            <!-- Suggested Coupons for Passenger -->
            <div style="font-size:11px; color:#475569; margin-bottom:5px; font-weight:600;">
              ✨ Suggested coupons for you (click to apply):
            </div>
            <div id="aiCouponChips_${formId}" style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px;">
              ${applicableCoupons.map(c => `
                <div class="ai-coupon-chip" data-code="${c.code}" style="cursor:pointer; background:#ffffff; border:1px dashed #16a34a; border-radius:6px; padding:3px 8px; font-size:11px; display:flex; align-items:center; gap:4px; transition:all 0.15s ease;" title="${c.description || ''}">
                  <span style="font-weight:700; color:#15803d;">${c.code}</span>
                  <span style="font-size:9px; background:#dcfce7; color:#166534; padding:1px 4px; border-radius:3px; font-weight:600;">${c.savings_text || c.title}</span>
                </div>
              `).join('')}
            </div>

            <!-- Coupon Input & Buttons -->
            <div style="display:flex; gap:6px;">
              <input type="text" id="aiCouponInput_${formId}" placeholder="Enter promo code (e.g. FIRST10)" style="flex:1; height:32px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 8px; font-size:12px; text-transform:uppercase; font-weight:700; background:#ffffff;" />
              <button type="button" id="aiBtnApplyCoupon_${formId}" style="padding:0 12px; height:32px; background:#16a34a; border:none; border-radius:6px; color:#ffffff; font-size:11px; font-weight:700; cursor:pointer;">
                Apply
              </button>
              <button type="button" id="aiBtnRemoveCoupon_${formId}" style="display:none; padding:0 8px; height:32px; background:#ef4444; border:none; border-radius:6px; color:#ffffff; font-size:11px; font-weight:700; cursor:pointer;" title="Remove Coupon">
                ✕
              </button>
            </div>
            <div id="aiCouponMsg_${formId}" style="display:none; font-size:11px; margin-top:6px; font-weight:600;"></div>

            <!-- Live Fare Breakdown with Coupon -->
            <div style="margin-top:8px; padding-top:6px; border-top:1px dashed #bbf7d0; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <span style="color:#64748b;">Base: </span>
                <span id="aiBaseFare_${formId}" style="font-weight:600; color:#334155;">₹${Number(data.fare_per_seat || 0).toFixed(2)}</span>
                <span id="aiDiscount_${formId}" style="display:none; color:#16a34a; font-weight:700; margin-left:6px;"></span>
              </div>
              <div>
                <span style="color:#64748b;">Payable: </span>
                <strong id="aiPayableFare_${formId}" style="font-size:13px; color:#b91c1c;">₹${Number(data.fare_per_seat || 0).toFixed(2)}</strong>
              </div>
            </div>
          </div>

          <button type="button" id="aiSubmit_${formId}" class="btn btn-primary btn-block" style="width:100%; height:42px; font-size:13px; font-weight:700; background:#d84e55; border:none; border-radius:8px; color:#fff; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px; box-shadow:0 3px 10px rgba(216,78,85,0.25);">
            <span>💳 Confirm Details & Proceed to Payment</span>
            <span id="aiBtnPayable_${formId}" style="background:rgba(255,255,255,0.25); padding:2px 8px; border-radius:4px; font-weight:800;">(₹${Number(data.fare_per_seat || 0).toFixed(2)})</span>
          </button>
        </div>
      `;
    }

    // Render bus cards if returned by search_bus
    let busesHtml = '';
    if (data.buses && data.buses.length > 0) {
      busesHtml = data.buses.slice(0, 3).map(b => {
        const depStr = (typeof formatTime === 'function') ? formatTime(b.departure_time) : (b.departure_time || '').slice(11, 16);
        const arrStr = (typeof formatTime === 'function' && b.arrival_time) ? ` | Arr: <strong>${formatTime(b.arrival_time)}</strong>` : '';
        return `
        <div class="ai-bus-card">
          <div class="ai-bus-header">
            <span>${b.operator_name}</span>
            <span style="color:#d84e55;">₹${Number(b.price || b.ticket_price || 0).toFixed(2)}</span>
          </div>
          <div class="ai-bus-details">
            ${b.bus_type} | Dep: <strong>${depStr}</strong>${arrStr} | ⭐ ${b.rating || 4.5}
          </div>
          <a href="seats.html?scheduleId=${b.bus_id || b.schedule_id}" class="btn btn-primary btn-sm" style="display:inline-block; font-size:11px; padding:4px 10px; text-decoration:none;">
            Select Seats &rarr;
          </a>
        </div>
      `;
      }).join('');
    }

    bubble.innerHTML = `
      ${toolHtml}
      <div>${replyText}</div>
      ${formHtml}
      ${bookedCardHtml}
      ${busesHtml}
      ${sourcesHtml}
    `;

    container.appendChild(bubble);

    // Attach interactive event listeners to the in-chat Form
    if (data.type === 'passenger_form_needed' || data.type === 'passenger_details_needed') {
      const pListContainer = document.getElementById(`aiPList_${formId}`);
      const numSelect = document.getElementById(`aiNumP_${formId}`);
      const submitBtn = document.getElementById(`aiSubmit_${formId}`);
      const toggleMapBtn = document.getElementById(`aiToggleSeatMap_${formId}`);
      const seatMapBox = document.getElementById(`aiSeatMapBox_${formId}`);
      const availSeats = data.available_seats || [];

      // Bus & Price details
      let farePerSeat = Number(data.fare_per_seat || 0);
      let activeBusId = data.bus_id;
      let activeBusNumber = data.bus_number || '';
      let appliedCoupon = null;
      let appliedDiscount = 0;

      const couponInput = document.getElementById(`aiCouponInput_${formId}`);
      const btnApplyCoupon = document.getElementById(`aiBtnApplyCoupon_${formId}`);
      const btnRemoveCoupon = document.getElementById(`aiBtnRemoveCoupon_${formId}`);
      const couponMsg = document.getElementById(`aiCouponMsg_${formId}`);
      const couponTag = document.getElementById(`aiCouponTag_${formId}`);
      const baseFareEl = document.getElementById(`aiBaseFare_${formId}`);
      const discountEl = document.getElementById(`aiDiscount_${formId}`);
      const payableFareEl = document.getElementById(`aiPayableFare_${formId}`);

      function computeDiscount(code, baseTotal) {
        const c = (code || '').toUpperCase().trim();
        if (c === 'FIRST10') {
          return { valid: true, discount: Math.min(200, Math.round(baseTotal * 0.10 * 100) / 100), msg: '10% discount applied!' };
        } else if (c === 'SAVE100') {
          if (baseTotal < 500) {
            return { valid: false, discount: 0, msg: 'SAVE100 requires booking of ₹500+' };
          }
          return { valid: true, discount: 100.0, msg: 'Flat ₹100 instant discount applied!' };
        } else if (c === 'SUMMER20') {
          return { valid: true, discount: Math.min(300, Math.round(baseTotal * 0.20 * 100) / 100), msg: '20% holiday discount applied!' };
        } else if (c === 'BUSGO50') {
          return { valid: true, discount: 50.0, msg: 'Flat ₹50 instant discount applied!' };
        }
        return { valid: false, discount: 0, msg: `Invalid coupon "${c}". Try FIRST10, SAVE100, SUMMER20, or BUSGO50.` };
      }

      function updateFareSummary() {
        const count = numSelect ? parseInt(numSelect.value, 10) : 1;
        const baseTotal = count * farePerSeat;
        if (baseFareEl) baseFareEl.innerText = `₹${baseTotal.toFixed(2)}`;

        const btnPayableEl = document.getElementById(`aiBtnPayable_${formId}`);

        if (appliedCoupon) {
          const res = computeDiscount(appliedCoupon, baseTotal);
          if (res.valid) {
            appliedDiscount = res.discount;
            const finalPayable = Math.max(0, baseTotal - appliedDiscount);
            if (discountEl) {
              discountEl.style.display = 'inline';
              discountEl.innerText = `-₹${appliedDiscount.toFixed(2)} (${appliedCoupon})`;
            }
            if (payableFareEl) payableFareEl.innerText = `₹${finalPayable.toFixed(2)}`;
            if (btnPayableEl) btnPayableEl.innerText = `(₹${finalPayable.toFixed(2)})`;
            else if (submitBtn) submitBtn.innerText = `💳 Confirm Details & Proceed to Payment (₹${finalPayable.toFixed(2)})`;

            if (couponTag) {
              couponTag.style.display = 'inline-block';
              couponTag.innerText = `✓ ${appliedCoupon} (-₹${appliedDiscount.toFixed(2)})`;
            }
          } else {
            appliedDiscount = 0;
            if (discountEl) discountEl.style.display = 'none';
            if (payableFareEl) payableFareEl.innerText = `₹${baseTotal.toFixed(2)}`;
            if (btnPayableEl) btnPayableEl.innerText = `(₹${baseTotal.toFixed(2)})`;
            else if (submitBtn) submitBtn.innerText = `💳 Confirm Details & Proceed to Payment (₹${baseTotal.toFixed(2)})`;

            if (couponMsg) {
              couponMsg.style.display = 'block';
              couponMsg.style.color = '#dc2626';
              couponMsg.innerText = res.msg;
            }
            if (couponTag) couponTag.style.display = 'none';
          }
        } else {
          appliedDiscount = 0;
          if (discountEl) discountEl.style.display = 'none';
          if (payableFareEl) payableFareEl.innerText = `₹${baseTotal.toFixed(2)}`;
          if (btnPayableEl) btnPayableEl.innerText = `(₹${baseTotal.toFixed(2)})`;
          else if (submitBtn) submitBtn.innerText = `💳 Confirm Details & Proceed to Payment (₹${baseTotal.toFixed(2)})`;

          if (couponTag) couponTag.style.display = 'none';
        }
      }

      function applyCouponCode(code) {
        if (!code) {
          if (couponMsg) {
            couponMsg.style.display = 'block';
            couponMsg.style.color = '#dc2626';
            couponMsg.innerText = 'Please enter a coupon code.';
          }
          return;
        }
        const count = numSelect ? parseInt(numSelect.value, 10) : 1;
        const baseTotal = count * farePerSeat;
        const res = computeDiscount(code, baseTotal);
        if (res.valid) {
          appliedCoupon = code.toUpperCase().trim();
          appliedDiscount = res.discount;
          if (couponInput) couponInput.value = appliedCoupon;
          if (couponMsg) {
            couponMsg.style.display = 'block';
            couponMsg.style.color = '#15803d';
            couponMsg.innerText = `✓ ${appliedCoupon} applied! ${res.msg} You saved ₹${appliedDiscount.toFixed(2)}.`;
          }
          if (btnRemoveCoupon) btnRemoveCoupon.style.display = 'inline-block';
          updateFareSummary();
        } else {
          if (couponMsg) {
            couponMsg.style.display = 'block';
            couponMsg.style.color = '#dc2626';
            couponMsg.innerText = res.msg;
          }
        }
      }

      // Hook up coupon chips
      const formEl = document.getElementById(formId);
      if (formEl) {
        formEl.querySelectorAll('.ai-coupon-chip').forEach(chip => {
          chip.addEventListener('click', () => {
            const code = chip.getAttribute('data-code');
            applyCouponCode(code);
          });
        });
      }

      // Hook up coupon input & apply/remove buttons
      if (btnApplyCoupon && couponInput) {
        btnApplyCoupon.addEventListener('click', () => {
          applyCouponCode(couponInput.value.trim());
        });
        couponInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            applyCouponCode(couponInput.value.trim());
          }
        });
      }
      if (btnRemoveCoupon) {
        btnRemoveCoupon.addEventListener('click', () => {
          appliedCoupon = null;
          appliedDiscount = 0;
          if (couponInput) couponInput.value = '';
          if (couponMsg) couponMsg.style.display = 'none';
          btnRemoveCoupon.style.display = 'none';
          updateFareSummary();
        });
      }

      // Hook up Multiple Buses Dropdown & Price Filter
      const busSelect = document.getElementById(`aiBusSelect_${formId}`);
      const priceFilter = document.getElementById(`aiPriceFilter_${formId}`);
      const chosenBusInfo = document.getElementById(`aiChosenBusInfo_${formId}`);
      const topPriceBadge = document.getElementById(`aiTopPriceBadge_${formId}`);
      const dropdownArea = document.getElementById(`aiBusDropdownArea_${formId}`);
      const countEl = document.getElementById(`aiPriceMatchCount_${formId}`);

      if (busSelect) {
        busSelect.addEventListener('change', () => {
          const selectedOpt = busSelect.selectedOptions[0];
          if (!selectedOpt) return;
          activeBusId = parseInt(selectedOpt.value, 10);
          activeBusNumber = selectedOpt.getAttribute('data-bus-number') || '';
          farePerSeat = parseFloat(selectedOpt.getAttribute('data-price') || farePerSeat);

          if (topPriceBadge) {
            topPriceBadge.innerText = `₹${farePerSeat.toFixed(2)}/seat | Bus #${activeBusNumber}`;
          }

          if (chosenBusInfo) {
            chosenBusInfo.innerHTML = `
              <span>🚍 <strong>${selectedOpt.getAttribute('data-operator')}</strong> (${selectedOpt.getAttribute('data-type')})</span>
              <span style="color:#b91c1c; font-weight:800; background:#fee2e2; padding:2px 8px; border-radius:4px; font-size:12px;">Bus #${activeBusNumber}</span>
            `;
          }

          updateFareSummary();
        });
      }

      if (priceFilter && busSelect) {
        priceFilter.addEventListener('change', () => {
          const filterVal = priceFilter.value;
          const maxP = filterVal === 'all' ? Infinity : parseFloat(filterVal);
          const matching = availableBuses.filter(b => b.price <= maxP);

          if (countEl) {
            countEl.innerText = `${matching.length} bus${matching.length === 1 ? '' : 'es'} match`;
          }

          // If 2 or more buses match that price specification, give user option to select bus
          if (matching.length >= 2) {
            if (dropdownArea) dropdownArea.style.display = 'block';
          } else {
            // Otherwise leave it
            if (dropdownArea) dropdownArea.style.display = 'none';
          }

          if (matching.length > 0) {
            busSelect.innerHTML = matching.map(b => `
              <option value="${b.bus_id}" data-price="${b.price}" data-bus-number="${b.bus_number}" data-operator="${b.operator_name}" data-type="${b.bus_type}" ${b.bus_id === activeBusId ? 'selected' : ''}>
                ${b.operator_name} (${b.bus_type}) | ₹${b.price.toFixed(2)} | Bus #${b.bus_number}
              </option>
            `).join('');

            // If activeBusId is not among matching, select first match
            if (!matching.some(b => b.bus_id === activeBusId)) {
              busSelect.value = matching[0].bus_id;
            }
            busSelect.dispatchEvent(new Event('change'));
          } else {
            // No buses under this specific budget
            if (chosenBusInfo) {
              const minBus = availableBuses.reduce((prev, curr) => curr.price < prev.price ? curr : prev, availableBuses[0]);
              chosenBusInfo.innerHTML = `
                <span style="color:#dc2626; font-size:11px;">⚠️ No buses under ₹${filterVal}. Lowest fare starts at <strong>₹${minBus.price.toFixed(2)}</strong> (${minBus.operator_name})</span>
                <span style="color:#b91c1c; font-weight:800; background:#fee2e2; padding:2px 8px; border-radius:4px; font-size:12px;">Bus #${minBus.bus_number}</span>
              `;
            }
          }
        });
      }

      function syncSeatMapColors() {
        if (!seatMapBox) return;
        const seatSelects = pListContainer ? pListContainer.querySelectorAll('.ai-input-seat') : [];
        const chosen = new Set();
        seatSelects.forEach(sel => {
          if (sel.value) chosen.add(sel.value);
        });

        seatMapBox.querySelectorAll('.ai-map-seat').forEach(cell => {
          const sNum = cell.getAttribute('data-seat');
          const isAvail = availSeats.some(s => s.seat_number === sNum);
          if (chosen.has(sNum)) {
            cell.style.background = '#d84e55';
            cell.style.color = '#ffffff';
            cell.style.borderColor = '#b91c1c';
          } else if (isAvail) {
            cell.style.background = '#dcfce7';
            cell.style.color = '#166534';
            cell.style.borderColor = '#86efac';
          }
        });
      }

      function updatePassengerFields(count) {
        if (!pListContainer) return;
        let html = '';
        for (let i = 1; i <= count; i++) {
          html += `
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-bottom:8px;">
              <div style="font-weight:700; font-size:12px; color:#334155; margin-bottom:6px; display:flex; justify-content:space-between;">
                <span>👤 Passenger ${i}:</span>
                <span style="font-size:11px; font-weight:600; color:#d84e55;">Seat Choice</span>
              </div>
              <div style="display:grid; grid-template-columns: 1.8fr 1fr 1.2fr 1.5fr; gap:6px;">
                <input type="text" class="ai-input-name" placeholder="Full Name" style="width:100%; height:32px; border:1px solid #cbd5e1; border-radius:6px; padding:4px 8px; font-size:12px;" required />
                <input type="number" class="ai-input-age" placeholder="Age" min="1" max="120" style="width:100%; height:32px; border:1px solid #cbd5e1; border-radius:6px; padding:4px 8px; font-size:12px;" required />
                <select class="ai-input-gender" style="width:100%; height:32px; border:1px solid #cbd5e1; border-radius:6px; padding:4px 4px; font-size:12px; background:#fff;">
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
                <select class="ai-input-seat" style="width:100%; height:32px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 4px; font-size:11px; background:#fff; font-weight:600; color:#1e293b;">
                  <option value="">⚡ Auto Seat</option>
                  ${availSeats.map(s => `<option value="${s.seat_number}">${s.seat_number} (${s.deck === 'upper' ? 'Upper' : 'Lower'})</option>`).join('')}
                </select>
              </div>
            </div>
          `;
        }
        pListContainer.innerHTML = html;

        pListContainer.querySelectorAll('.ai-input-seat').forEach(sel => {
          sel.addEventListener('change', () => {
            syncSeatMapColors();
          });
        });
        syncSeatMapColors();

        container.scrollTop = container.scrollHeight;
        updateFareSummary();
      }

      if (numSelect) {
        numSelect.addEventListener('change', (e) => {
          updatePassengerFields(parseInt(e.target.value, 10));
        });
        updatePassengerFields(1);
      }

      // Toggle visual seat map
      if (toggleMapBtn && seatMapBox) {
        toggleMapBtn.addEventListener('click', () => {
          const isHidden = seatMapBox.style.display === 'none';
          seatMapBox.style.display = isHidden ? 'block' : 'none';
          toggleMapBtn.innerText = isHidden ? '🔼 Hide Bus Seat Map' : '💺 View Bus Seat Map & Pick Comfort Seats';
          container.scrollTop = container.scrollHeight;
        });

        // Click on map seats to assign to passenger dropdowns
        seatMapBox.querySelectorAll('.ai-map-seat').forEach(cell => {
          cell.addEventListener('click', () => {
            const seatNum = cell.getAttribute('data-seat');
            const seatObj = availSeats.find(s => s.seat_number === seatNum);
            if (!seatObj) return;

            const seatSelects = pListContainer.querySelectorAll('.ai-input-seat');
            let assigned = false;

            // Check if this seat is already assigned, if so unassign
            for (let sel of seatSelects) {
              if (sel.value === seatNum) {
                sel.value = '';
                assigned = true;
                break;
              }
            }

            // Otherwise assign to first empty dropdown
            if (!assigned) {
              for (let sel of seatSelects) {
                if (!sel.value) {
                  sel.value = seatNum;
                  break;
                }
              }
            }
            syncSeatMapColors();
          });
        });
      }

      if (submitBtn) {
        submitBtn.addEventListener('click', () => {
          const names = pListContainer.querySelectorAll('.ai-input-name');
          const ages = pListContainer.querySelectorAll('.ai-input-age');
          const genders = pListContainer.querySelectorAll('.ai-input-gender');
          const seats = pListContainer.querySelectorAll('.ai-input-seat');
          const bpSelect = document.getElementById(`aiBp_${formId}`);
          const dpSelect = document.getElementById(`aiDp_${formId}`);

          const passengers = [];
          for (let i = 0; i < names.length; i++) {
            const nameVal = names[i].value.trim();
            const ageVal = parseInt(ages[i].value, 10);
            const genderVal = genders[i].value;
            const seatVal = seats[i] ? seats[i].value : '';

            if (!nameVal) {
              alert(`Please enter the full name for Passenger ${i + 1}`);
              names[i].focus();
              return;
            }
            if (!ageVal || isNaN(ageVal) || ageVal < 1 || ageVal > 120) {
              alert(`Please enter a valid age (1-120) for Passenger ${i + 1}`);
              ages[i].focus();
              return;
            }
            passengers.push({
              name: nameVal,
              age: ageVal,
              gender: genderVal,
              seat_number: seatVal
            });
          }

          // Check duplicate seat selection across passengers
          const selectedSeats = new Set();
          for (let i = 0; i < passengers.length; i++) {
            const s = passengers[i].seat_number;
            if (s) {
              if (selectedSeats.has(s)) {
                alert(`Seat "${s}" is chosen more than once. Please select different seats or use "Auto Seat".`);
                return;
              }
              selectedSeats.add(s);
            }
          }

          const boardingPoint = bpSelect ? bpSelect.value : '';
          const droppingPoint = dpSelect ? dpSelect.value : '';

          // Directly reserve seats and navigate straight to payment (no extra chat message)
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<span>⏳ Reserving seats & redirecting to payment...</span>';
          submitBtn.style.background = '#16a34a';

          const user = (typeof getUser === 'function') ? getUser() : null;
          const userId = user ? user.user_id : 1;
          const API_ENDPOINT = (typeof API_BASE !== 'undefined') ? `${API_BASE}/chat` : '/api/chat';

          const payload = {
            message: 'Confirmed booking details',
            user_id: userId,
            passengers: passengers,
            num_passengers: passengers.length,
            boarding_point: boardingPoint,
            dropping_point: droppingPoint,
            coupon_code: appliedCoupon || '',
            discount: appliedDiscount,
            source: data.source,
            destination: data.destination,
            date: data.date,
            bus_id: activeBusId || data.bus_id,
            bus_number: activeBusNumber || data.bus_number || ''
          };

          fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          })
          .then(res => res.json())
          .then(resData => {
            if (resData && resData.booking && resData.booking.booking_id) {
              const b = resData.booking;
              b.bus_number = b.bus_number || activeBusNumber;
              try {
                sessionStorage.setItem('busgo_last_booking', JSON.stringify(b));
              } catch (e) {}

              // Direct instant redirection to secure payment checkout
              window.location.href = `payment.html?bookingId=${b.booking_id}`;
            } else if (resData && resData.reply) {
              alert(resData.reply.replace(/\*\*/g, ''));
              submitBtn.disabled = false;
              submitBtn.innerHTML = '<span>💳 Confirm Details & Proceed to Payment</span>';
              submitBtn.style.background = '#d84e55';
            } else {
              alert('Could not complete seat reservation. Please try again.');
              submitBtn.disabled = false;
              submitBtn.innerHTML = '<span>💳 Confirm Details & Proceed to Payment</span>';
              submitBtn.style.background = '#d84e55';
            }
          })
          .catch(err => {
            console.error('Reservation error:', err);
            alert('Server unreachable. Please verify Flask backend is active.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>💳 Confirm Details & Proceed to Payment</span>';
            submitBtn.style.background = '#d84e55';
          });
        });
      }
    }
  }

})();
