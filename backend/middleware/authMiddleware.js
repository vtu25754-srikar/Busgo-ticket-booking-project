const jwt = require('jsonwebtoken');

function verifyToken(req, res, next) {
  try {
    const authHeader = req.headers['authorization'] || req.headers['Authorization'];
    if (!authHeader) {
      return res.status(401).json({
        success: false,
        message: 'Access denied. No authorization token provided.'
      });
    }

    const tokenParts = authHeader.split(' ');
    if (tokenParts.length !== 2 || tokenParts[0] !== 'Bearer') {
      return res.status(401).json({
        success: false,
        message: 'Invalid token format. Expected "Bearer <token>".'
      });
    }

    const token = tokenParts[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'busgo_jwt_fallback_secret');

    // Attach user payload: userId, email, role, name
    req.user = decoded;
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token expired. Please log in again.'
      });
    }
    return res.status(401).json({
      success: false,
      message: 'Invalid or forged token.'
    });
  }
}

// Optional auth: attaches user if token is present, continues otherwise
function optionalAuth(req, res, next) {
  try {
    const authHeader = req.headers['authorization'] || req.headers['Authorization'];
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.split(' ')[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET || 'busgo_jwt_fallback_secret');
      req.user = decoded;
    }
  } catch (err) {
    // ignore token errors for optional auth
  }
  next();
}

module.exports = {
  verifyToken,
  optionalAuth
};
