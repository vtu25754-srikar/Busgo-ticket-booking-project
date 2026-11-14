/**
 * BUSGO - Authentication JS (Login & Register)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Check if session expired query param is present
  const params = new URLSearchParams(window.location.search);
  if (params.get('session_expired')) {
    showToast('Your session has expired. Please login again.', 'info');
  }

  // --- Login Form Handler ---
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      if (!email || !password) {
        showToast('Please enter both email and password.', 'error');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerText = 'Logging in...';

      try {
        const response = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          localStorage.setItem('busgo_token', data.token);
          localStorage.setItem('busgo_user', JSON.stringify(data.user));

          showToast('Login successful! Redirecting...', 'success');

          setTimeout(() => {
            if (data.user.role === 'admin') {
              window.location.href = 'admin-dashboard.html';
            } else if (data.user.role === 'operator') {
              window.location.href = 'operator-dashboard.html';
            } else {
              // Check if redirect query exists (e.g. from seat booking)
              const redirect = params.get('redirect') || 'index.html';
              window.location.href = redirect;
            }
          }, 800);
        } else {
          showToast(data.message || 'Invalid login credentials.', 'error');
        }
      } catch (err) {
        console.error('Login error:', err);
        showToast('Failed to connect to authentication server.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Login to BUSGO';
      }
    });
  }

  // --- Registration Form Handler ---
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    // Role selection toggle
    const roleRadios = document.querySelectorAll('input[name="role"]');
    const operatorFields = document.getElementById('operatorFields');

    roleRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (operatorFields) {
          operatorFields.style.display = e.target.value === 'operator' ? 'block' : 'none';
        }
      });
    });

    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = document.getElementById('name').value.trim();
      const email = document.getElementById('email').value.trim();
      const phone = document.getElementById('phone').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;
      const role = document.querySelector('input[name="role"]:checked')?.value || 'customer';
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      // Validation
      if (!name || !email || !phone || !password) {
        showToast('Please fill out all required fields.', 'error');
        return;
      }

      if (phone.length < 10) {
        showToast('Please enter a valid 10-digit mobile number.', 'error');
        return;
      }

      if (password.length < 6) {
        showToast('Password must be at least 6 characters long.', 'error');
        return;
      }

      if (password !== confirmPassword) {
        showToast('Passwords do not match.', 'error');
        return;
      }

      const payload = { name, email, phone, password, role };

      if (role === 'operator') {
        payload.companyName = document.getElementById('companyName')?.value.trim() || `${name} Travels`;
        payload.licenseNumber = document.getElementById('licenseNumber')?.value.trim() || '';
      }

      submitBtn.disabled = true;
      submitBtn.innerText = 'Creating account...';

      try {
        const response = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
          localStorage.setItem('busgo_token', data.token);
          localStorage.setItem('busgo_user', JSON.stringify(data.user));

          showToast('Account created successfully! Redirecting...', 'success');

          setTimeout(() => {
            if (data.user.role === 'operator') {
              window.location.href = 'operator-dashboard.html';
            } else {
              window.location.href = 'index.html';
            }
          }, 800);
        } else {
          showToast(data.message || 'Registration failed.', 'error');
        }
      } catch (err) {
        console.error('Registration error:', err);
        showToast('Could not register account. Server connection error.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Create Account';
      }
    });
  }
});
