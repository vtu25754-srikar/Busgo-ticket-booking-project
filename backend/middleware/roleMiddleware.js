/**
 * Role-based authorization middleware
 * @param  {...string} allowedRoles e.g. 'admin', 'operator', 'customer'
 */
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required.'
      });
    }

    const userRole = (req.user.role || '').toLowerCase();
    const hasRole = allowedRoles.some(role => role.toLowerCase() === userRole);

    if (!hasRole) {
      return res.status(403).json({
        success: false,
        message: `Forbidden. Requires one of [${allowedRoles.join(', ')}] role.`
      });
    }

    next();
  };
}

module.exports = {
  requireRole
};
