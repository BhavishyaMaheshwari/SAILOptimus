import mongoose from 'mongoose';
const { Schema } = mongoose;

const decisionSchema = new Schema({
  train_id: { type: String, required: true },
  action: { type: String, enum: ['PROCEED', 'HOLD'], required: true },
  details: { type: String }
});

const generatedScheduleSchema = new Schema({
  section_id: { type: String, required: true },
  decisions: [decisionSchema],
  objective_function_used: {
    type: String,
    default: 'strict_priority'
  }
}, { timestamps: true });

const GeneratedSchedule = mongoose.model('GeneratedSchedule', generatedScheduleSchema);
export default GeneratedSchedule;
