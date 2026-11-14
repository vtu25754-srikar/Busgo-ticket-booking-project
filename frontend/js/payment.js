/**
 * BUSGO - Online Payment Processing JS
 * Interactive Multi-Mode Payment Gateway (UPI, Cards, NetBanking, Wallets)
 * Includes Bank 3D Secure / OTP Verification Flow & Razorpay Fallback
 */

let paymentOrderData = null;
let bookingId = null;
let activeTab = 'upi';
let selectedBank = 'HDFC';
let sessionTimerSeconds = 600; // 10 minutes
let timerInterval = null;
let gatewayTimer20 = null;
let remaining20Sec = 20;
let gatewayTimer5 = null;
let remaining5Sec = 5;

document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  bookingId = params.get('bookingId');

  if (!bookingId) {
    const lastBookingStr = sessionStorage.getItem('busgo_last_booking');
    if (lastBookingStr) {
      try {
        const lb = JSON.parse(lastBookingStr);
        bookingId = lb.bookingId || lb.booking_id;
      } catch (e) {}
    }
  }

  // If no bookingId and user is not logged in, redirect to login
  if (!isLoggedIn() && !bookingId) {
    window.location.href = `login.html?redirect=${encodeURIComponent(window.location.href)}`;
    return;
  }

  if (!bookingId) {
    showToast('Missing booking ID. Redirecting to home...', 'error');
    setTimeout(() => window.location.href = 'index.html', 1200);
    return;
  }

  // Start 10-minute session countdown
  startSessionTimer();

  // Initialize Payment Order & Review Details
  await initializePaymentOrder(bookingId);

  // Pay button listener
  const payBtn = document.getElementById('btnPayNow');
  if (payBtn) {
    payBtn.addEventListener('click', handlePaymentClick);
  }

  // Setup card number formatting & brand detection
  setupCardFormatting();
});

/**
 * 10-Minute Checkout Countdown Timer
 */
function startSessionTimer() {
  const display = document.getElementById('sessionTimerDisplay');
  if (!display) return;

  timerInterval = setInterval(() => {
    if (sessionTimerSeconds <= 0) {
      clearInterval(timerInterval);
      display.innerText = '00:00 (Expired)';
      showToast('Your seat reservation window has expired. Please select seats again.', 'error');
      setTimeout(() => window.location.href = 'index.html', 2500);
      return;
    }

    sessionTimerSeconds--;
    const mins = Math.floor(sessionTimerSeconds / 60);
    const secs = sessionTimerSeconds % 60;
    display.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, 1000);
}

/**
 * Switch payment mode tabs
 */
function switchPaymentTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.pay-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
  });
  document.querySelectorAll('.pay-tab-content').forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabName}`);
  });
}

function toggleUpiMode(mode) {
  const idSec = document.getElementById('upiIdSection');
  const qrSec = document.getElementById('upiQrSection');
  if (idSec) idSec.style.display = mode === 'id' ? 'block' : 'none';
  if (qrSec) qrSec.style.display = mode === 'qr' ? 'block' : 'none';
}

function selectBank(el, bankCode) {
  selectedBank = bankCode;
  document.querySelectorAll('.bank-item').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
}

/**
 * Live card number formatting and logo detection
 */
function setupCardFormatting() {
  const cardInput = document.getElementById('cardNumberInput');
  const brandIcon = document.getElementById('cardBrandIcon');
  if (!cardInput) return;

  cardInput.addEventListener('input', (e) => {
    let val = e.target.value.replace(/\D/g, '');
    let formatted = val.match(/.{1,4}/g)?.join(' ') || val;
    cardInput.value = formatted.substring(0, 19);

    // Brand detection
    if (val.startsWith('4')) {
      brandIcon.innerText = '💳 Visa';
    } else if (val.startsWith('5')) {
      brandIcon.innerText = '💳 MasterCard';
    } else if (val.startsWith('6') || val.startsWith('8')) {
      brandIcon.innerText = '💳 RuPay';
    } else {
      brandIcon.innerText = '💳';
    }
  });

  const expiryInput = document.getElementById('cardExpiryInput');
  if (expiryInput) {
    expiryInput.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '');
      if (val.length >= 2) {
        val = val.substring(0, 2) + '/' + val.substring(2, 4);
      }
      expiryInput.value = val.substring(0, 5);
    });
  }
}

/**
 * Initialize payment order
 */
async function initializePaymentOrder(bId) {
  try {
    const res = await authFetch(`${API_BASE}/payments/create-order`, {
      method: 'POST',
      body: JSON.stringify({ bookingId: bId })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      paymentOrderData = data;
      renderPaymentDetails(data);
    } else {
      showToast(data.message || 'Failed to initialize payment gateway.', 'error');
    }
  } catch (err) {
    console.error('Payment order error:', err);
    showToast('Payment system unreachable.', 'error');
  }
}

function renderPaymentDetails(data) {
  const b = data.booking || {};
  const amount = Number(data.amount || 0);

  // PNR
  const pnrEl = document.getElementById('paymentBookingPnr');
  if (pnrEl) pnrEl.innerText = b.pnr || `BG${b.bookingId}`;

  // Amounts
  const amtDisplay = document.getElementById('paymentAmountDisplay');
  const payBtnAmt = document.getElementById('payBtnAmount');
  if (amtDisplay) amtDisplay.innerText = formatCurrency(amount);
  if (payBtnAmt) payBtnAmt.innerText = formatCurrency(amount);

  // Review Summary
  const busNameEl = document.getElementById('reviewBusName');
  if (busNameEl) busNameEl.innerText = `${b.operator_name || 'Express'} Luxury (${b.bus_type || 'AC Sleeper'})`;

  const routeEl = document.getElementById('reviewRoute');
  if (routeEl) routeEl.innerHTML = `<strong>${b.source || 'Origin'}</strong> &rarr; <strong>${b.destination || 'Destination'}</strong>`;

  const dateTimeEl = document.getElementById('reviewDateTime');
  if (dateTimeEl) dateTimeEl.innerText = `Departure: ${formatTime(b.departure_time)} | ${formatDate(b.departure_time)}`;

  const bPointEl = document.getElementById('reviewBoardingPoint');
  if (bPointEl) bPointEl.innerText = b.boarding_point || `${b.source} Central Bus Stand`;

  const dPointEl = document.getElementById('reviewDroppingPoint');
  if (dPointEl) dPointEl.innerText = b.dropping_point || `${b.destination} Main Terminal`;

  const passNameEl = document.getElementById('reviewPassengerName');
  if (passNameEl) passNameEl.innerText = b.passenger_name || 'Traveler';

  const seatNoEl = document.getElementById('reviewSeatNumber');
  if (seatNoEl) seatNoEl.innerText = b.seat_number || 'L1';

  const busNoEl = document.getElementById('reviewBusNumber');
  if (busNoEl) busNoEl.innerText = b.bus_number || 'KA-09-F-4521';

  // Fare calculations
  const base = Math.max(0, amount - 50);
  const baseEl = document.getElementById('reviewBaseFare');
  if (baseEl) baseEl.innerText = formatCurrency(base);

  const taxesEl = document.getElementById('reviewTaxes');
  if (taxesEl) taxesEl.innerText = formatCurrency(Math.round(base * 0.05));

  // Masked phone in modal
  const phone = data.prefill?.phone || '9876543210';
  const maskedEl = document.getElementById('modalMaskedPhone');
  if (maskedEl) maskedEl.innerText = `•••• ${phone.slice(-4)}`;

  const modalAmtEl = document.getElementById('modalAmountDisplay');
  if (modalAmtEl) modalAmtEl.innerText = formatCurrency(amount);
}

/**
 * Handle "Pay & Confirm" button click
 */
function handlePaymentClick() {
  // If user provided a live Razorpay key
  if (window.Razorpay && paymentOrderData?.keyId && !paymentOrderData.keyId.includes('rzp_test_busgo')) {
    executeLiveRazorpay();
  } else {
    // Open Bank 3D Secure / OTP Simulator Modal
    openPaymentModal();
  }
}

function openPaymentModal() {
  const modal = document.getElementById('paymentModal');
  if (modal) {
    modal.classList.add('active');
    modal.style.display = 'flex';
    modal.style.opacity = '1';
    modal.style.visibility = 'visible';
    start20SecGatewayTimer();
  }
}

function closePaymentModal() {
  const modal = document.getElementById('paymentModal');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
    modal.style.opacity = '0';
    modal.style.visibility = 'hidden';
  }
  if (gatewayTimer20) clearInterval(gatewayTimer20);
  if (gatewayTimer5) clearInterval(gatewayTimer5);
}

/**
 * 20-Second Gateway Authorization Phase
 */
function start20SecGatewayTimer() {
  if (gatewayTimer20) clearInterval(gatewayTimer20);
  if (gatewayTimer5) clearInterval(gatewayTimer5);

  remaining20Sec = 20;

  const phase20 = document.getElementById('phase20SecCountdown');
  const phase5 = document.getElementById('phase5SecProcessing');
  const circle = document.getElementById('authTimerCircle');
  const bar = document.getElementById('countdown20Bar');
  const verifyBtn = document.getElementById('btnVerifyPayment');
  const stepLabel = document.getElementById('gatewayStepLabel');

  if (phase20) phase20.style.display = 'block';
  if (phase5) phase5.style.display = 'none';
  if (stepLabel) stepLabel.innerText = 'Authorization (20s)';
  
  if (verifyBtn) {
    verifyBtn.disabled = true;
    verifyBtn.style.background = '#94a3b8';
    verifyBtn.style.cursor = 'not-allowed';
    verifyBtn.innerText = '⏳ Verifying Security Protocol (20s)...';
  }
  if (circle) {
    circle.innerText = '20';
    circle.style.background = '#eff6ff';
    circle.style.color = '#2563eb';
    circle.style.borderColor = '#bfdbfe';
  }
  if (bar) bar.style.width = '0%';

  gatewayTimer20 = setInterval(() => {
    remaining20Sec--;
    if (circle) circle.innerText = remaining20Sec;
    if (bar) {
      const progress = ((20 - remaining20Sec) / 20) * 100;
      bar.style.width = `${progress}%`;
    }

    if (remaining20Sec > 0) {
      if (verifyBtn) {
        verifyBtn.innerText = `⏳ Verifying Security Protocol (${remaining20Sec}s)...`;
      }
    } else {
      clearInterval(gatewayTimer20);
      unlockVerifyButton();
    }
  }, 1000);
}

function unlockVerifyButton() {
  const circle = document.getElementById('authTimerCircle');
  const bar = document.getElementById('countdown20Bar');
  const verifyBtn = document.getElementById('btnVerifyPayment');
  const stepLabel = document.getElementById('gatewayStepLabel');

  if (circle) {
    circle.innerText = '✓';
    circle.style.background = '#dcfce7';
    circle.style.color = '#15803d';
    circle.style.borderColor = '#86efac';
  }
  if (bar) bar.style.width = '100%';
  if (stepLabel) stepLabel.innerText = 'Ready to Verify';

  if (verifyBtn) {
    verifyBtn.disabled = false;
    verifyBtn.style.background = '#16a34a';
    verifyBtn.style.color = '#ffffff';
    verifyBtn.style.cursor = 'pointer';
    verifyBtn.innerHTML = '✓ Verify Payment & Proceed (Click Here)';
  }
}

function skip20SecTimer() {
  if (gatewayTimer20) clearInterval(gatewayTimer20);
  remaining20Sec = 0;
  unlockVerifyButton();
  showToast('Demo Mode: Fast-forwarded 20s security timer', 'info');
}

function triggerAutoPrint(bId) {
  try {
    let printFrame = document.getElementById('ticketPrintIframe');
    if (!printFrame) {
      printFrame = document.createElement('iframe');
      printFrame.id = 'ticketPrintIframe';
      printFrame.style.position = 'fixed';
      printFrame.style.right = '0';
      printFrame.style.bottom = '0';
      printFrame.style.width = '0';
      printFrame.style.height = '0';
      printFrame.style.border = '0';
      document.body.appendChild(printFrame);
    }
    printFrame.src = `${API_BASE}/bookings/${bId}/download-ticket`;
  } catch (e) {
    console.warn('Hidden print iframe error:', e);
  }
}

/**
 * 5-Second Verification & Auto-Print Phase
 */
async function handleVerifyButtonClick() {
  const phase20 = document.getElementById('phase20SecCountdown');
  const phase5 = document.getElementById('phase5SecProcessing');
  const circle5 = document.getElementById('processing5SecCircle');
  const bar5 = document.getElementById('countdown5Bar');
  const text5 = document.getElementById('proc5SecText');
  const stepLabel = document.getElementById('gatewayStepLabel');

  if (phase20) phase20.style.display = 'none';
  if (phase5) phase5.style.display = 'block';
  if (stepLabel) stepLabel.innerText = 'Final Verification (5s)';

  remaining5Sec = 5;
  if (circle5) {
    circle5.innerText = '5';
    circle5.style.background = '#f0fdf4';
    circle5.style.color = '#16a34a';
    circle5.style.borderColor = '#86efac';
  }
  if (text5) text5.innerText = '5 seconds';
  if (bar5) bar5.style.width = '0%';

  const paymentMethodText = activeTab === 'upi' ? 'UPI' : (activeTab === 'card' ? 'Card' : (activeTab === 'netbanking' ? `NetBanking (${selectedBank})` : 'Wallet'));
  const mockPaymentData = {
    razorpay_order_id: paymentOrderData?.orderId || `order_${Date.now()}`,
    razorpay_payment_id: `pay_${Date.now()}_busgo`,
    razorpay_signature: `sig_verified_${Date.now()}`
  };

  // Trigger verify on backend
  const verifyPromise = verifyBackendPayment(mockPaymentData, paymentMethodText);

  if (gatewayTimer5) clearInterval(gatewayTimer5);
  gatewayTimer5 = setInterval(async () => {
    remaining5Sec--;
    if (circle5) circle5.innerText = remaining5Sec > 0 ? remaining5Sec : '✓';
    if (text5) text5.innerText = remaining5Sec > 0 ? `${remaining5Sec} seconds` : 'Finalizing...';
    if (bar5) {
      const progress = ((5 - remaining5Sec) / 5) * 100;
      bar5.style.width = `${progress}%`;
    }

    if (remaining5Sec <= 0) {
      clearInterval(gatewayTimer5);
      if (circle5) circle5.innerText = '🖨️';
      if (text5) text5.innerText = 'Printing ticket now...';

      const verifyResult = await verifyPromise;
      if (verifyResult && verifyResult.success) {
        const pnr = verifyResult.booking?.pnr || paymentOrderData?.booking?.pnr || 'BGCONFIRMED';

        // Auto-print ticket in a new window/tab and via iframe
        try {
          triggerAutoPrint(bookingId);
          window.open(`${API_BASE}/bookings/${bookingId}/download-ticket`, '_blank');
        } catch (e) {
          console.warn('Popup blocked, ticket still downloadable from confirmation page:', e);
        }

        showToast('Payment successful! Printing ticket...', 'success');
        setTimeout(() => {
          window.location.href = `confirmation.html?bookingId=${bookingId}&pnr=${pnr}&autoPrint=1`;
        }, 1200);
      } else {
        showToast('Payment verification failed. Please try again.', 'error');
        if (phase20) phase20.style.display = 'block';
        if (phase5) phase5.style.display = 'none';
        unlockVerifyButton();
      }
    }
  }, 1000);
}

/**
 * Send signature / token to backend for confirmation
 */
async function verifyBackendPayment(paymentData, method) {
  try {
    const res = await authFetch(`${API_BASE}/payments/verify`, {
      method: 'POST',
      body: JSON.stringify({
        bookingId: bookingId,
        razorpay_order_id: paymentData.razorpay_order_id,
        razorpay_payment_id: paymentData.razorpay_payment_id,
        razorpay_signature: paymentData.razorpay_signature,
        paymentMethod: method
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      if (timerInterval) clearInterval(timerInterval);
      return data;
    } else {
      showToast(data.message || 'Payment verification failed.', 'error');
      return null;
    }
  } catch (err) {
    console.error('Verify payment error:', err);
    showToast('Payment gateway network error. Please try again.', 'error');
    return null;
  }
}

/**
 * Live Razorpay execution if merchant keys configured
 */
function executeLiveRazorpay() {
  const options = {
    key: paymentOrderData.keyId,
    amount: paymentOrderData.amountInPaise,
    currency: 'INR',
    name: 'BUSGO India',
    description: `Bus Ticket Booking (PNR: ${paymentOrderData.booking.pnr})`,
    order_id: paymentOrderData.orderId,
    handler: async function (response) {
      await verifyBackendPayment(response, 'Razorpay');
    },
    prefill: {
      name: paymentOrderData.prefill?.name,
      email: paymentOrderData.prefill?.email,
      contact: paymentOrderData.prefill?.phone
    },
    theme: {
      color: '#D84E55'
    }
  };

  const rzp = new window.Razorpay(options);
  rzp.on('payment.failed', function (response) {
    showToast(`Payment failed: ${response.error.description}`, 'error');
  });
  rzp.open();
}
