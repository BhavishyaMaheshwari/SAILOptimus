import express from 'express';
import cors from 'cors';
import http from 'http';
import { Server } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';

import connectDB from './config/database.js';
import sectionRoutes from './routes/section.routes.js';


import scheduleRoutes from './routes/schedule.routes.js';
// Import the new simulation route we will create
import simulationRoutes from './routes/simulation.routes.js';

import LiveTrainState from './models/liveTrainState.model.js';

// Map Routes
import mapRoutes from './routes/map.routes.js';
// const mapRoutes = require('./routes/map.routes')

//Train Routes

import trainRoutes from './routes/train.routes.js';

//User Routes
import userRoutes from './routes/user.routes.js'; // Make sure this path is correct
// Initialize Express app

const app = express();

//& 2. Use the cors middleware right after you initialize express
app.use(cors());

//Basic Server Setup
const server = http.createServer(app); // Create HTTP server
// const io = new Server(server); // Attach Socket.IO to the server
// --- FIX: Add CORS configuration to Socket.IO ---
// This tells Socket.IO to allow connections from your frontend application.
const io = new Server(server, {
  cors: {
    origin: "http://localhost:8080", // IMPORTANT: Change this to your frontend's port (e.g., 3000, 5173)
    methods: ["GET", "POST"]
  }
});
// ---------------------------------------------
// fix for ES modules __dirname

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Connect to Database
connectDB();

// Middleware to parse JSON bodies
app.use(express.json());
// Serve static files from the 'public' folder
// Mount Routers
app.use('/api/sections', sectionRoutes);
// app.use('/api/trains', trainRoutes);
app.use('/api/schedules', scheduleRoutes);
app.use('/api/simulations', simulationRoutes); // Use the new route

app.use(express.static(path.join(__dirname, 'public'))); //& frontend build files


// // --- WebSocket Logic ---
// io.on('connection', (socket) => {
//   console.log('A user connected to WebSocket'); //log 1
//   socket.on('disconnect', () => {
//     console.log('User disconnected');
//   });
// })
// THIS IS THE CRITICAL LINE
// It tells Express: "For any URL that starts with '/api/users', use the routes defined in userRoutes."
app.use('/api/users', userRoutes);


// This tells your app that any request starting with '/api/maps'
// should be handled by the mapRoutes file.
app.use('/api/maps', mapRoutes);
// This tell your app that any request startinf with '/api/trains
app.use('/api/trains', trainRoutes);

// Tell Express to use your router for any requests that start with /api/delays



// --- WebSocket Logic ---
// --- WebSocket Logic ---
io.on('connection', async (socket) => {
  console.log('--- A user connected to WebSocket ---'); // Log 1

  try {
    console.log('1. About to query the database for live train states...'); // Log 2

    const initialStates = await LiveTrainState.find({}).populate('train_id');

    console.log('2. Query finished. Found states:', JSON.stringify(initialStates, null, 2)); // Log 3

    socket.emit('initialTrainStates', initialStates);

    console.log('3. Event "initialTrainStates" was successfully emitted to the client.'); // Log 4

  } catch (error) {
    console.error('!!! ERROR fetching initial train states:', error); // Log 5 (Error)
  }

  socket.on('disconnect', () => {
    console.log('--- User disconnected ---');
  });
});
// Prefer env PORT; if not set, use 5001 (5000 can be taken by macOS Control Center)
const PORT = Number(process.env.PORT) || 5005;
server.listen(PORT, () => {
  console.log(`Server running in ES6 Module mode on port ${PORT}`);
});

// Export io so it can be used in other files
export { io };



// train id 68c8eff75e2a796afa4d35a4
// section "_id": "68c8f0c45e2a796afa4d35ac"
