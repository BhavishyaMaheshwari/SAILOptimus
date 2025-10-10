import express from 'express';
import { createScheduleForSection } from '../controllers/schedule.controller.js';

const router = express.Router();

// Note the route parameter :sectionId
router.route('/section/:sectionId').post(createScheduleForSection);

export default router;