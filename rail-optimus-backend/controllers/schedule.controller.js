// import { generateSimpleSchedule } from '../services/scheduler.service.js';
import { generateUtilityBasedSchedule } from '../services/advancedScheduler.service.js';
import GeneratedSchedule from '../models/generatedSchedule.model.js';
import Section from '../models/section.model.js';

// @desc    Generate and save a new schedule for a section
// @route   POST /api/schedules/section/:sectionId
export const createScheduleForSection = async (req, res) => {
  try {
    const { sectionId } = req.params;

    // Verify the section exists
    const section = await Section.findById(sectionId);
    if (!section) {
      return res.status(404).json({ success: false, error: 'Section not found' });
    }

    // Call the scheduling service to get the decisions
    // --- SWAP THE ENGINE ---
    // Old call: const decisions = await generateSimpleSchedule(sectionId);
    // const decisions = await generateSimpleSchedule(sectionId);

    // New call to our "AI" engine:
    const decisions = await generateUtilityBasedSchedule(sectionId);


    // Save the new schedule to the database
    const newSchedule = await GeneratedSchedule.create({
      section_id: section.section_id,
      decisions: decisions,
    });

    res.status(201).json({ success: true, data: newSchedule });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
};