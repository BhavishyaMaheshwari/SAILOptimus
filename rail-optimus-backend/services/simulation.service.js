import LiveTrainState from '../models/liveTrainState.model.js';
import Section from '../models/section.model.js';

/**
 * Advances a train to the next block in its section.
 * @param {string} liveTrainStateId - The _id of the live train state to advance.
 * @returns {object} The updated live train state document.
 */
export const advanceTrain = async (liveTrainStateId) => {
  // 1. Find the train's current state
  const trainState = await LiveTrainState.findById(liveTrainStateId);
  if (!trainState) throw new Error('Live train state not found');

  // 2. Find the section to get the track block layout
  const section = await Section.findById(trainState.section_id);
  if (!section) throw new Error('Section not found for this train');

  const trackBlocks = section.track_blocks;
  const currentBlockIndex = trackBlocks.findIndex(
    block => block.block_id === trainState.current_block_id
  );

  // 3. Determine the next block
  if (currentBlockIndex === -1) throw new Error('Current block not found in section layout');

  if (currentBlockIndex < trackBlocks.length - 1) {
    // There is a next block, so move the train
    const nextBlock = trackBlocks[currentBlockIndex + 1];
    trainState.current_block_id = nextBlock.block_id;
    trainState.status = 'RUNNING';
  } else {
    // This is the last block, so halt the train
    trainState.status = 'HALTED';
  }

  // 4. Save the updated state to the database
  await trainState.save();
  
  // 5. Populate train_id to send full info to the frontend
  const updatedState = await LiveTrainState.findById(liveTrainStateId).populate('train_id');
  return updatedState;
};