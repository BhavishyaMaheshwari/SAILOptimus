import User from '../models/user.model.js';
import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';
import catchasync from '../utils/catchasync.js'; // <-- IMPORT CATCHASYNC
import AppError from '../utils/appError.js'; // <-- We'll create this small error utility next

// Configure environment variables
dotenv.config();

// --- Helper function to sign a JWT token ---
// This creates a secure token that the user can use to prove they are logged in.
const signToken = id => {
  // It's crucial to use environment variables for your secret and expiry time.
  const secret = process.env.JWT_SECRET || 'a-very-secure-default-secret-key-that-should-be-changed';
  const expiresIn = process.env.JWT_EXPIRES_IN || '90d';
  
  return jwt.sign({ id }, secret, { expiresIn });
};

// --- Controller function for user signup ---

//&new
// --- Controller function for user signup ---
export const signup = catchasync(async (req, res, next) => {
    // --- CHECKPOINT 1: Did the data arrive from the frontend? ---
    console.log('1. Received signup request with body:', req.body);
    
    // Create a new user with the data from the request body.
    // The password will be automatically hashed by the middleware in your User model.
    const newUser = await User.create({
        name: req.body.name,
        username: req.body.username,
        password: req.body.password,
        passwordConfirm: req.body.passwordConfirm,
        section: req.body.section,
        role: req.body.role, // Optional, will default to 'controller'
    });
    
    // --- CHECKPOINT 2: Did MongoDB return a user object after saving? ---
    console.log('2. User object created by MongoDB:', newUser);

    // Create a token for the new user.
    const token = signToken(newUser._id);

    // Remove the password from the output before sending the response.
    newUser.password = undefined;

    res.status(201).json({
        status: 'success',
        token,
        data: {
            user: newUser,
        },
    });
});
// export const signup = catchasync(async (req, res,next) => {
//   // --- CHECKPOINT 1: Did the data arrive from the frontend? ---
//   console.log('1. Received signup request with body:', req.body)

//     // Create a new user with the data from the request body.
//     // The password will be automatically hashed by the middleware in your User model. //& Now we pass passwordConfirm to the create method
//     const newUser = await User.create({
//       name: req.body.name,
//       username: req.body.username,
//       password: req.body.password,
//       passwordconfirm: req.body.passwordconfirm,
//       section: req.body.section,
//       role: req.body.role, // Optional, will default to 'controller'
//     });
//     // --- CHECKPOINT 2: Did MongoDB return a user object after saving? ---
//     // This is the most important log. If you see this, the user WAS saved.
//     console.log('2. User object created by MongoDB:', newUser);

//     // Create a token for the new user.
//     const token = signToken(newUser._id);

//     // Remove the password from the output before sending the response.
//     newUser.password = undefined;

//     res.status(201).json({
//       status: 'success',
//       token,
//       data: {
//         user: newUser,
//       },
//     });
//   // } catch (error) {
//   //   // --- CHECKPOINT 3: Did the database throw an error? ---
//   //   // If you see this, the problem is likely a validation rule in your User model.
//   //   console.error('3. ERROR during User.create:', error);
//   //   // This will catch errors, such as if the username already exists.
//   //   res.status(400).json({ status: 'fail', message: error.message });

// });

// --- Controller function for user login ---
export const login = catchasync(async (req, res,next) => {
  // try {
    const { username, password } = req.body;

    // 1) Check if username and password were provided in the request.
    if (!username || !password) {
      return res.status(400).json({ status: 'fail', message: 'Please provide username and password.' });
    }

    // 2) Find the user in the database and explicitly include the password for comparison.
    const user = await User.findOne({ username }).select('+password');

    // 3) Check if the user exists and if the provided password is correct.
    // This calls the 'correctPassword' method you defined in your user model.
    if (!user || !(await user.correctPassword(password, user.password))) {
      // return res.status(401).json({ status: 'fail', message: 'Incorrect username or password.' });
      // Use AppError for a consistent error-handling approach.
      return next(new AppError('Incorrect username or password.', 401));
    }

    // 4) If everything is correct, create and send the token to the client.
    const token = signToken(user._id);

    // Remove the password from the output before sending the response.
    user.password = undefined;

    res.status(200).json({
      status: 'success',
      token,
      data: {
        user,
      },
    });
  // } catch (error) {
  //   res.status(500).json({ status: 'error', message: 'An internal server error occurred.' });
  // }
});

