// import express from 'express';
// import { createTrain, getAllTrains } from '../controllers/train.controller.js';

// const router = express.Router();

// router.route('/')
//   .post(createTrain)
//   .get(getAllTrains);

// export default router;

import express from 'express';
// Import the specific controller function we need.
import { getTrainsBySection } from '../controllers/train.controller.js';

// Create a new router instance.
const trainroutes = express.Router();

// Define the route.
// This will handle dynamic GET requests like '/api/trains/agra' or '/api/trains/assam'.
// The ':section' part of the URL is captured and passed to the controller.
trainroutes.get('/:section', getTrainsBySection);

// Export the router so it can be used in your main app.js file.
export default trainroutes;

