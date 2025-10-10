import mongoose from 'mongoose';
const { Schema } = mongoose;

const liveTrainStateSchema = new Schema({
  // Link to the static Train document
  train_id: {
    type: Schema.Types.ObjectId,
    ref: 'Train', // This tells Mongoose to link to the 'Train' collection
    required: true,
  },
  // Link to the section the train is currently in
  section_id: {
    type: Schema.Types.ObjectId,
    ref: 'Section',
    required: true,
  },
  current_block_id: {
    type: String,
    required: true,
  },
  current_speed_kmph: {
    type: Number,
    default: 0,
  },
  status: {
    type: String,
    enum: ['RUNNING', 'HALTED', 'WAITING_SIGNAL'],
    default: 'HALTED',
  },
  delay_seconds: {
    type: Number,
    default: 0,
  },
}, { timestamps: true });

const LiveTrainState = mongoose.model('LiveTrainState', liveTrainStateSchema);
export default LiveTrainState;