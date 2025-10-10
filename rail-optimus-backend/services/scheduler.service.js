import LiveTrainState from '../models/liveTrainState.model.js';
import Section from '../models/section.model.js';

/**
 * A simple scheduling engine that decides train movements based on strict priority.
 * @param {string} sectionId - The ID of the section to schedule.
 * @returns {Array<object>} An array of decision objects.
 */
export const generateSimpleSchedule = async (sectionId) => {
  // 1. Fetch all trains currently waiting for a signal in the specified section
  const waitingTrains = await LiveTrainState.find({
    section_id: sectionId,
    status: 'WAITING_SIGNAL',
  })
  .populate('train_id'); // <-- This is crucial! It fetches the linked Train document's data.

  if (waitingTrains.length === 0) {
    return [{ train_id: 'None', action: 'HOLD', details: 'No trains are waiting for a signal.' }];
  }

  [cite_start]// 2. Sort the trains by priority (lower number = higher priority) [cite: 68]
  waitingTrains.sort((a, b) => a.train_id.priority - b.train_id.priority);

  // 3. For this simple engine, we only make a decision for the highest-priority train.
  const highestPriorityTrain = waitingTrains[0];
  const trainInfo = highestPriorityTrain.train_id;

  // In a real system, you would check if the next block is clear.
  // For this simulation, we'll just approve the highest priority train.
  // We'll create "HOLD" decisions for all others.
  
  const decisions = [];

  // Decision for the highest priority train
  decisions.push({
    train_id: trainInfo.train_id,
    action: 'PROCEED',
    details: `Proceeding as it has the highest priority (${trainInfo.priority}).`
  });

  // Decisions for all other waiting trains
  for (let i = 1; i < waitingTrains.length; i++) {
    const otherTrainInfo = waitingTrains[i].train_id;
    decisions.push({
      train_id: otherTrainInfo.train_id,
      action: 'HOLD',
      details: `Holding for higher priority train (${highestPriorityTrain.train_id.train_id}) to pass.`
    });
  }

  return decisions;
};