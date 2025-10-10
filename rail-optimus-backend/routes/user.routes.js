import express from 'express';
import { signup, login } from '../controllers/auth.controller.js';
import { protect, restrictTo } from '../middleware/authMiddleware.js';

const userRoutes = express.Router();

// When the main server file uses this with '/api/users', this route becomes '/api/users/login'
userRoutes.post('/login', login);

// This route becomes '/api/users/signup'
userRoutes.post('/signup', signup);

export default userRoutes;