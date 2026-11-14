/**
 * BUSGO - User Profile Management JS
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!isLoggedIn()) {
    window.location.href = 'login.html?redirect=profile.html';
    return;
  }

  await loadUserProfile();

  // Profile update form
  const profileForm = document.getElementById('updateProfileForm');
  if (profileForm) {
    profileForm.addEventListener('submit', handleProfileUpdate);
  }

  // Password change form
  const passwordForm = document.getElementById('changePasswordForm');
  if (passwordForm) {
    passwordForm.addEventListener('submit', handlePasswordChange);
  }
});

async function loadUserProfile() {
  try {
    const res = await authFetch(`${API_BASE}/auth/profile`);
    const data = await res.json();

    if (res.ok && data.success) {
      const u = data.user;
      document.getElementById('profileName').value = u.name || '';
      document.getElementById('profileEmail').value = u.email || '';
      document.getElementById('profilePhone').value = u.phone || '';
      document.getElementById('profileRoleBadge').innerText = (u.role || 'customer').toUpperCase();

      const initials = (u.name || 'User')
        .split(' ')
        .map(n => n[0])
        .join('')
        .substring(0, 2)
        .toUpperCase();
      document.getElementById('profileAvatarBig').innerText = initials;
      document.getElementById('profileGreetingName').innerText = u.name;
    }
  } catch (err) {
    console.error('Error loading profile:', err);
  }
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const name = document.getElementById('profileName').value.trim();
  const phone = document.getElementById('profilePhone').value.trim();

  if (!name || !phone) {
    showToast('Name and phone are required.', 'error');
    return;
  }

  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;

  try {
    const res = await authFetch(`${API_BASE}/auth/profile`, {
      method: 'PUT',
      body: JSON.stringify({ name, phone })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      showToast('Profile updated successfully!', 'success');
      const currentUser = getUser();
      if (currentUser) {
        currentUser.name = name;
        currentUser.phone = phone;
        localStorage.setItem('busgo_user', JSON.stringify(currentUser));
        updateNavbar();
      }
    } else {
      showToast(data.message || 'Could not update profile.', 'error');
    }
  } catch (err) {
    showToast('Error updating profile.', 'error');
  } finally {
    submitBtn.disabled = false;
  }
}

async function handlePasswordChange(e) {
  e.preventDefault();
  const oldPassword = document.getElementById('oldPassword').value;
  const newPassword = document.getElementById('newPassword').value;
  const confirmNewPassword = document.getElementById('confirmNewPassword').value;

  if (newPassword.length < 6) {
    showToast('New password must be at least 6 characters long.', 'error');
    return;
  }

  if (newPassword !== confirmNewPassword) {
    showToast('New passwords do not match.', 'error');
    return;
  }

  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;

  try {
    const res = await authFetch(`${API_BASE}/auth/change-password`, {
      method: 'PUT',
      body: JSON.stringify({ oldPassword, newPassword })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      showToast('Password changed successfully!', 'success');
      e.target.reset();
    } else {
      showToast(data.message || 'Could not change password.', 'error');
    }
  } catch (err) {
    showToast('Error changing password.', 'error');
  } finally {
    submitBtn.disabled = false;
  }
}
