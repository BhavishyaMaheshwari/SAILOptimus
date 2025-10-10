import { advanceTrain } from '../services/simulation.service.js';
import { io } from '../app.js'; // Import the io object

// @desc    Advance a train to its next block
// @route   POST /api/simulations/advance/:liveTrainStateId
export const advanceTrainController = async (req, res) => {
  try {
    const { liveTrainStateId } = req.params;
    const updatedTrainState = await advanceTrain(liveTrainStateId);

    // EMIT a WebSocket event to all connected clients!
    io.emit('trainUpdate', updatedTrainState);

    res.status(200).json({ success: true, data: updatedTrainState });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
};