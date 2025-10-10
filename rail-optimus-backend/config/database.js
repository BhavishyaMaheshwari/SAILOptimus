import mongoose from 'mongoose';
import 'dotenv/config'; // Loads variables from .env into process.env

const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    console.log('MongoDB Connected Successfully!');
  } catch (error) {
    console.error('MongoDB Connection Failed:', error.message);
    process.exit(1); // Exit process with failure
  }
};

export default connectDB;