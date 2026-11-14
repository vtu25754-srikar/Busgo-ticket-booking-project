/**
 * BUSGO - Core Frontend JavaScript Utilities
 */

const API_BASE = window.location.origin.includes('localhost') 
  ? `${window.location.origin}/api` 
  : 'http://localhost:5000/api';

// Authentication Helpers
function getToken() {
  return localStorage.getItem('busgo_token');
}

function getUser() {
  const userStr = localStorage.getItem('busgo_user');
  try {
    return userStr ? JSON.parse(userStr) : null;
  } catch (e) {
    return null;
  }
}

function isLoggedIn() {
  return !!getToken();
}

function logout() {
  localStorage.removeItem('busgo_token');
  localStorage.removeItem('busgo_user');
  sessionStorage.clear();
  showToast('Logged out successfully', 'info');
  setTimeout(() => {
    window.location.href = 'login.html';
  }, 500);
}

/**
 * Authenticated Fetch wrapper
 */
async function authFetch(url, options = {}) {
  const token = getToken();
  options.headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, options);

    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('busgo_token');
      localStorage.removeItem('busgo_user');
      window.location.href = 'login.html?session_expired=1';
      return response;
    }

    return response;
  } catch (error) {
    console.error('[authFetch] Network or API error:', error);
    showToast('Network error. Please check your connection.', 'error');
    throw error;
  }
}

/**
 * Global Toast Notification
 */
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <span style="cursor:pointer; margin-left:12px; font-weight:bold;" onclick="this.parentElement.remove()">&times;</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Formatting Helpers
 */
function formatCurrency(amount) {
  const num = Number(amount || 0);
  return '₹' + num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

function formatTime(timeStr) {
  if (!timeStr) return '';
  let str = String(timeStr).trim();
  // Strip date portion if present e.g. "2026-11-14 22:00:00" or "2026-11-14T22:00:00"
  if (str.includes('T')) {
    str = str.split('T')[1];
  } else if (str.includes(' ')) {
    str = str.split(' ')[1];
  }
  str = str.split('.')[0].split('+')[0].split('Z')[0].trim();

  const parts = str.split(':');
  if (parts.length < 2) return timeStr;
  let hours = parseInt(parts[0], 10);
  if (isNaN(hours)) return timeStr;
  let minutes = parseInt(parts[1], 10);
  if (isNaN(minutes)) minutes = 0;

  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 becomes 12
  const minStr = String(minutes).padStart(2, '0');
  return `${hours}:${minStr} ${ampm}`;
}

/**
 * Robust arrival time calculator across the entire frontend:
 * Given departure time and duration (in hours, e.g. 8.5 or "8h 30m" or minutes),
 * returns { arrivalHour, arrivalMin, formattedArrival, isNextDay, computedTimeStr }
 */
function calculateArrivalTime(departureTimeStr, durationVal) {
  if (!departureTimeStr) return { formattedArrival: '', isNextDay: false };
  let str = String(departureTimeStr).trim();

  // Extract HH:MM
  let timeOnly = str;
  if (timeOnly.includes('T')) timeOnly = timeOnly.split('T')[1];
  else if (timeOnly.includes(' ')) timeOnly = timeOnly.split(' ')[1];
  timeOnly = timeOnly.split('.')[0];

  const parts = timeOnly.split(':');
  const depH = parseInt(parts[0], 10) || 0;
  const depM = parseInt(parts[1], 10) || 0;

  // Parse durationVal into total minutes
  let durMins = 0;
  if (typeof durationVal === 'number') {
    durMins = Math.round(durationVal * 60);
  } else if (typeof durationVal === 'string') {
    const dStr = durationVal.toLowerCase();
    if (dStr.includes('h')) {
      const hPart = parseInt(dStr.split('h')[0].trim(), 10) || 0;
      let mPart = 0;
      if (dStr.includes('m')) {
        mPart = parseInt(dStr.split('h')[1].replace('m', '').trim(), 10) || 0;
      }
      durMins = hPart * 60 + mPart;
    } else {
      durMins = parseInt(dStr, 10) || 510; // default 8.5h
    }
  } else {
    durMins = 510;
  }

  const depTotalMins = depH * 60 + depM;
  const arrTotalMins = depTotalMins + durMins;
  const isNextDay = arrTotalMins >= 1440; // 24 * 60 = 1440
  const arrH = Math.floor(arrTotalMins / 60) % 24;
  const arrM = arrTotalMins % 60;

  const ampm = arrH >= 12 ? 'PM' : 'AM';
  const displayH = arrH % 12 ? arrH % 12 : 12;
  const displayM = String(arrM).padStart(2, '0');
  const formattedArrival = `${displayH}:${displayM} ${ampm}`;

  return {
    arrivalHour: arrH,
    arrivalMin: arrM,
    formattedArrival,
    isNextDay,
    computedTimeStr: `${String(arrH).padStart(2, '0')}:${displayM}:00`
  };
}

/**
 * Navbar UI updater according to auth state
 */
function updateNavbar() {
  const navActions = document.querySelector('.nav-actions');
  if (!navActions) return;

  const user = getUser();

  if (user && isLoggedIn()) {
    let dashboardLink = '';
    if (user.role === 'admin') {
      dashboardLink = `<a href="admin-dashboard.html" class="nav-link" style="color:var(--primary); font-weight:600;">Admin Panel</a>`;
    } else if (user.role === 'operator') {
      dashboardLink = `<a href="operator-dashboard.html" class="nav-link" style="color:var(--primary); font-weight:600;">Operator Portal</a>`;
    }

    const initials = (user.name || 'User')
      .split(' ')
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();

    navActions.innerHTML = `
      ${dashboardLink}
      <a href="mybookings.html" class="nav-link">My Bookings</a>
      <div class="user-pill" onclick="window.location.href='profile.html'">
        <div class="user-avatar">${initials}</div>
        <span>${user.name ? user.name.split(' ')[0] : 'Account'}</span>
      </div>
      <button onclick="logout()" class="btn btn-secondary btn-sm" title="Log out">Logout</button>
    `;
  } else {
    navActions.innerHTML = `
      <a href="login.html" class="btn btn-secondary btn-sm">Login</a>
      <a href="register.html" class="btn btn-primary btn-sm">Register</a>
    `;
  }
}

// Initialise navbar when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  updateNavbar();
});
