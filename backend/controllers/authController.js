const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { pool } = require('../config/db');
const { sendWelcomeEmail } = require('../utils/emailService');

/**
 * Register a new user (Customer or Operator)
 */
async function register(req, res) {
  try {
    const { name, email, phone, password, role = 'customer', companyName, licenseNumber, address } = req.body;

    // Validation
    if (!name || !email || !phone || !password) {
      return res.status(400).json({
        success: false,
        message: 'Name, email, phone, and password are required fields.'
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        message: 'Password must be at least 6 characters long.'
      });
    }

    // Check duplicate email or phone
    const [existingUsers] = await pool.query(
      'SELECT user_id, email, phone FROM users WHERE email = ? OR phone = ? LIMIT 1',
      [email.trim().toLowerCase(), phone.trim()]
    );

    if (existingUsers.length > 0) {
      const existing = existingUsers[0];
      const field = existing.email === email.trim().toLowerCase() ? 'Email' : 'Phone number';
      return res.status(409).json({
        success: false,
        message: `${field} is already registered. Please login or use a different ${field.toLowerCase()}.`
      });
    }

    // Hash password
    const saltRounds = 10;
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    const userRole = ['customer', 'operator'].includes(role) ? role : 'customer';

    // Insert user into DB
    const [userResult] = await pool.query(
      `INSERT INTO users (name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)`,
      [name.trim(), email.trim().toLowerCase(), phone.trim(), hashedPassword, userRole]
    );

    const userId = userResult.insertId;

    // If operator, create operator profile
    let operatorId = null;
    if (userRole === 'operator') {
      const compName = companyName || `${name.trim()} Travels`;
      const [opResult] = await pool.query(
        `INSERT INTO operators (user_id, company_name, email, phone, license_number, address, status)
         VALUES (?, ?, ?, ?, ?, ?, 'approved')`,
        [userId, compName, email.trim().toLowerCase(), phone.trim(), licenseNumber || `LIC-${Date.now()}`, address || '', 'approved']
      );
      operatorId = opResult.insertId;
    }

    // Generate JWT token
    const token = jwt.sign(
      {
        userId,
        email: email.trim().toLowerCase(),
        role: userRole,
        name: name.trim(),
        operatorId
      },
      process.env.JWT_SECRET || 'busgo_jwt_fallback_secret',
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    // Send welcome email in background
    sendWelcomeEmail(email.trim().toLowerCase(), name.trim()).catch(err => {
      console.error('[Auth] Welcome email error:', err.message);
    });

    return res.status(201).json({
      success: true,
      message: 'Account created successfully!',
      token,
      user: {
        userId,
        name: name.trim(),
        email: email.trim().toLowerCase(),
        phone: phone.trim(),
        role: userRole,
        operatorId
      }
    });
  } catch (error) {
    console.error('[Auth] Register error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error while registering user.'
    });
  }
}

/**
 * User login
 */
async function login(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password are required.'
      });
    }

    // Find user
    const [users] = await pool.query(
      `SELECT u.*, o.operator_id, o.company_name, o.status as operator_status
       FROM users u
       LEFT JOIN operators o ON u.user_id = o.user_id
       WHERE u.email = ? LIMIT 1`,
      [email.trim().toLowerCase()]
    );

    if (users.length === 0) {
      return res.status(401).json({
        success: false,
        message: 'Invalid email or password.'
      });
    }

    const user = users[0];

    if (!user.is_active) {
      return res.status(403).json({
        success: false,
        message: 'Your account has been deactivated. Please contact support.'
      });
    }

    // Compare password
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({
        success: false,
        message: 'Invalid email or password.'
      });
    }

    // Generate JWT token
    const token = jwt.sign(
      {
        userId: user.user_id,
        email: user.email,
        role: user.role,
        name: user.name,
        operatorId: user.operator_id || null
      },
      process.env.JWT_SECRET || 'busgo_jwt_fallback_secret',
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    return res.json({
      success: true,
      message: 'Logged in successfully!',
      token,
      user: {
        userId: user.user_id,
        name: user.name,
        email: user.email,
        phone: user.phone,
        role: user.role,
        operatorId: user.operator_id || null,
        companyName: user.company_name || null
      }
    });
  } catch (error) {
    console.error('[Auth] Login error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error during login.'
    });
  }
}

/**
 * Get current user profile
 */
async function getProfile(req, res) {
  try {
    const [users] = await pool.query(
      `SELECT u.user_id, u.name, u.email, u.phone, u.role, u.is_active, u.created_at,
              o.operator_id, o.company_name, o.license_number, o.status as operator_status
       FROM users u
       LEFT JOIN operators o ON u.user_id = o.user_id
       WHERE u.user_id = ?`,
      [req.user.userId]
    );

    if (users.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'User profile not found.'
      });
    }

    return res.json({
      success: true,
      user: users[0]
    });
  } catch (error) {
    console.error('[Auth] getProfile error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to retrieve profile.'
    });
  }
}

/**
 * Update user profile
 */
async function updateProfile(req, res) {
  try {
    const { name, phone } = req.body;

    if (!name || !phone) {
      return res.status(400).json({
        success: false,
        message: 'Name and phone are required.'
      });
    }

    // Check duplicate phone
    const [existing] = await pool.query(
      'SELECT user_id FROM users WHERE phone = ? AND user_id != ? LIMIT 1',
      [phone.trim(), req.user.userId]
    );

    if (existing.length > 0) {
      return res.status(409).json({
        success: false,
        message: 'Phone number already in use by another account.'
      });
    }

    await pool.query(
      'UPDATE users SET name = ?, phone = ? WHERE user_id = ?',
      [name.trim(), phone.trim(), req.user.userId]
    );

    return res.json({
      success: true,
      message: 'Profile updated successfully!'
    });
  } catch (error) {
    console.error('[Auth] updateProfile error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to update profile.'
    });
  }
}

/**
 * Change account password
 */
async function changePassword(req, res) {
  try {
    const { oldPassword, newPassword } = req.body;

    if (!oldPassword || !newPassword) {
      return res.status(400).json({
        success: false,
        message: 'Current password and new password are required.'
      });
    }

    if (newPassword.length < 6) {
      return res.status(400).json({
        success: false,
        message: 'New password must be at least 6 characters long.'
      });
    }

    const [users] = await pool.query(
      'SELECT password FROM users WHERE user_id = ?',
      [req.user.userId]
    );

    if (users.length === 0) {
      return res.status(404).json({ success: false, message: 'User not found.' });
    }

    const isMatch = await bcrypt.compare(oldPassword, users[0].password);
    if (!isMatch) {
      return res.status(400).json({
        success: false,
        message: 'Current password does not match.'
      });
    }

    const hashedNew = await bcrypt.hash(newPassword, 10);
    await pool.query(
      'UPDATE users SET password = ? WHERE user_id = ?',
      [hashedNew, req.user.userId]
    );

    return res.json({
      success: true,
      message: 'Password changed successfully!'
    });
  } catch (error) {
    console.error('[Auth] changePassword error:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to change password.'
    });
  }
}

module.exports = {
  register,
  login,
  getProfile,
  updateProfile,
  changePassword
};
