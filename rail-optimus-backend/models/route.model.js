import mongoose from 'mongoose';
const { Schema } = mongoose;

const stopSchema = new Schema({
  source_stn_name: { type: String },
  source_stn_code: { type: String },
  arrive: { type: String },
  depart: { type: String },
  distance: { type: String },
  day: { type: String },
  zone: { type: String },
});

const routeSchema = new Schema({
  train_no: { type: String, required: true, unique: true },
  train_name: { type: String },
  priority: { type: Number, required: true },
  source_stn_code: { type: String },
  dstn_stn_code: { type: String },
  stops: [stopSchema]
});

const Route = mongoose.model('Routeagra', routeSchema);
export default Route;