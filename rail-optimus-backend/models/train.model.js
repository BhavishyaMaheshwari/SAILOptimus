import mongoose from 'mongoose';
const { Schema } = mongoose;

const trainSchema = new Schema({
  train_id_string: { type: String, required: true, unique: true },
  train_no: { type: String, required: true },
  train_name: { type: String },
  train_type: {
    type: String,
    required: true,
    enum: ['express', 'suburban', 'freight', 'maintenance', 'special']
  },
  priority: { type: Number, required: true },
  source_stn_code: { type: String },
  dstn_stn_code: { type: String },
  running_days: { type: String },
}, { timestamps: true });

const Train = mongoose.model('Trainagra', trainSchema);
export default Train;