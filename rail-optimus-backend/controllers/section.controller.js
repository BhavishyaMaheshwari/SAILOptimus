// Note the .js extension is required for local module imports
import Section from '../models/section.model.js';

// @desc    Create a new section
// @route   POST /api/sections
export const createSection = async (req, res) => {
  try {
    const section = await Section.create(req.body);
    res.status(201).json({ success: true, data: section });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
};

// @desc    Get all sections
// @route   GET /api/sections
export const getAllSections = async (req, res) => {
  try {
    const sections = await Section.find({});
    res.status(200).json({ success: true, count: sections.length, data: sections });
  } catch (error) {
    res.status(500).json({ success: false, error: 'Server Error' });
  }
};