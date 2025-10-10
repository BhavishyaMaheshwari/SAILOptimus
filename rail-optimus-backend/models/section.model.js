import mongoose from 'mongoose';
const { Schema } = mongoose;

const trackBlockSchema = new Schema({
  block_id: { type: String, required: true },
  length_m: { type: Number, required: true },
  max_speed_kmph: { type: Number, required: true } //
});

const platformSchema = new Schema({
    platform_id: { type: String, required: true },
    length_m: { type: Number, required: true } //
});

const sectionSchema = new Schema({
  section_id: { type: String, required: true, unique: true }, //
  num_tracks: { type: Number, default: 1 }, //
  track_blocks: [trackBlockSchema], //
  platforms: [platformSchema], //
  line_capacity: { type: Number } //
}, { timestamps: true });

const Section = mongoose.model('Section', sectionSchema);
export default Section;