const express = require('express');
const jwt = require('jsonwebtoken');
const cors = require('cors');

const app = express();

app.use(cors());
app.use(express.json());

// --- Simplified Default User ---
const DEFAULT_USER = {
  _id: '1',
  username: 'controller01',
  password: 'password123',
  name: 'Default Controller'
};

const JWT_SECRET = 'your-very-secret-key';

// --- Login Endpoint ---
app.post('/api/users/login', (req, res) => {
  const { username, password } = req.body;

  if (username === DEFAULT_USER.username && password === DEFAULT_USER.password) {
    const userPayload = { ...DEFAULT_USER };
    delete userPayload.password;

    const token = jwt.sign(userPayload, JWT_SECRET, { expiresIn: '1h' });

    res.status(200).json({
      status: 'success',
      data: {
        user: userPayload,
        token
      }
    });
  } else {
    res.status(401).json({
      status: 'fail',
      message: 'Invalid username or password'
    });
  }
});

// --- Start the Server ---
const PORT = 5005;
app.listen(PORT, () => {
  console.log(`🚀 Server is running on http://localhost:${PORT}`);
});