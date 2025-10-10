import LiveTrainState from '../models/liveTrainState.model.js';

/**
 * An advanced scheduling engine that uses a utility score to make decisions.
 * The goal is to select the train with the LOWEST score (highest urgency).
 * @param {string} sectionId - The ID of the section to schedule.
 * @returns {Array<object>} An array of decision objects.
 */
export const generateUtilityBasedSchedule = async (sectionId) => {
  const waitingTrains = await LiveTrainState.find({
    section_id: sectionId,
    status: 'WAITING_SIGNAL',
  }).populate('train_id');

  if (waitingTrains.length === 0) {
    return [{ train_id: 'None', action: 'HOLD', details: 'No trains are waiting.' }];
  }

  // --- The "AI" Logic: Utility Score Calculation ---
  // These weights can be tuned. They are based on your research[cite: 177].
  const weights = {
    priority: 100, // A lower priority number (e.g., 1 for express) is better
    delay: 1,      // Each second of delay adds to the urgency
  };

  const scoredTrains = waitingTrains.map(trainState => {
    const train = trainState.train_id;
    // Lower score is better (more urgent)
    const score = (train.priority * weights.priority) + (trainState.delay_seconds * weights.delay);
    return {
      ...trainState.toObject(), // Convert mongoose doc to plain object
      score: score,
    };
  });

  // Sort trains by score in ascending order (lowest score first)
  scoredTrains.sort((a, b) => a.score - b.score);

  const bestTrain = scoredTrains[0];
  const decisions = [];

  // Decision for the best-scored train
  decisions.push({
    train_id: bestTrain.train_id.train_id,
    action: 'PROCEED',
    details: `Proceeding due to the lowest utility score (${bestTrain.score.toFixed(0)}).`
  });

  // Decisions for all other trains
  for (let i = 1; i < scoredTrains.length; i++) {
    const otherTrain = scoredTrains[i];
    decisions.push({
      train_id: otherTrain.train_id.train_id,
      action: 'HOLD',
      details: `Holding for a more urgent train to pass. Score: ${otherTrain.score.toFixed(0)}.`
    });
  }

  return decisions;
};