import jwt from 'jsonwebtoken';
import User from '../models/user.model.js';

// This middleware checks if the user is logged in
export const protect = async (req, res, next) => {
    // ... your existing logic to verify the JWT token ...
    // After you decode the token, attach the user to the request
    req.user = await User.findById(decoded.id).select('-password');
    next();
};

// NEW: This middleware checks if the user has a specific role
export const restrictTo = (...roles) => {
    return (req, res, next) => {
        // req.user.role is available because the 'protect' middleware ran first
        if (!roles.includes(req.user.role)) {
            // 403 Forbidden: You are not authorized to perform this action
            return res.status(403).json({ 
                status: 'fail', 
                message: 'You do not have permission to perform this action.'
            });
        }
        next();
    };
};