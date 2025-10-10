import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';

const userSchema = new mongoose.Schema({
  username: {
    type: String,
    required: [true, 'Username is required'],
    unique: true,
    trim: true,
    lowercase: true,
  },
  password: {
    type: String,
    required: [true, 'Password is required'],
    select: false, // Prevents the password from being sent in queries by default
  },
  passwordConfirm: {
    type: String,
    required: [true, 'Please confirm your password'],
    validate: {
      // This only works on CREATE and SAVE!
      validator: function(el) {
        return el === this.password;
      },
      message: 'Passwords are not the same!',
    }
  },
  name: {
    type: String,
    required: [true, 'Name is required'],
  },
  section: {
    type: String,
    required: [true, 'Section is required'],
  },
  // role: {
  //   type: String,
  //   enum: ['controller', 'admin'],
  //   default: 'controller',
  // },
}, { timestamps: true });

// --- Password Hashing Middleware ---
// This function automatically runs before a new user document is saved.
userSchema.pre('save', async function(next) {
  // Only run this function if the password was actually modified
  if (!this.isModified('password')) return next();

  // Hash the password with a "salt" of 12 rounds
  this.password = await bcrypt.hash(this.password, 12);
  //Delete the confirmation field so it's not saved to the DB
  this.passwordConfirm = undefined;   
  next();

});

// --- Instance Method to Compare Passwords ---
// This adds a new method to every user document that allows us to safely check the password during login.
userSchema.methods.correctPassword = async function(candidatePassword, userPassword) {
  return await bcrypt.compare(candidatePassword, userPassword);
};

const User = mongoose.model('User', userSchema);

export default User;

