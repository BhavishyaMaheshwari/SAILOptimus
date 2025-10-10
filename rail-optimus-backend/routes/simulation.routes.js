import express from 'express';
import { advanceTrainController } from '../controllers/simulation.controller.js';

const router = express.Router();

router.route('/advance/:liveTrainStateId').post(advanceTrainController);

export default router;