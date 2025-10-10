import mongoose from 'mongoose';
import axios from 'axios';
import 'dotenv/config';

import Train from './models/train.model.js';
import Route from './models/route.model.js';

const SECTIONS_TO_FETCH = [
  { from: 'AGC', to: 'GWL', description: 'Agra to Gwalior' },
];
const LOCAL_API_BASE_URL = 'http://localhost:3000';

function getTrainAttributes(trainInfo) {
  const name = trainInfo.train_name.toUpperCase();
  const apiType = trainInfo.type ? trainInfo.type.toUpperCase() : '';

  if (name.includes('RAJDHANI') || name.includes('SHATABDI') || name.includes('VANDE BHARAT') || name.includes('DURONTO')) {
    return { priority: 0, train_type: 'express' };
  }
  if (apiType === 'SUPERFAST' || name.includes('SF') || name.includes('EXP')) {
    return { priority: 1, train_type: 'express' };
  }
  return { priority: 2, train_type: 'suburban' };
}

const seedDatabase = async () => {
  console.log('--- Starting Database Seeding Process ---');
  await mongoose.connect(process.env.MONGO_URI);
  console.log('Database connected.');

  console.log('Clearing existing data...');
  await Train.deleteMany({});
  await Route.deleteMany({});
  console.log('Cleared existing Train and Route data.');

  const uniqueTrainNumbers = new Set();

  console.log('\n--- PHASE 1: Discovering Unique Trains ---');
  for (const section of SECTIONS_TO_FETCH) {
    try {
      const response = await axios.get(`${LOCAL_API_BASE_URL}/trains/betweenStations`, { params: { from: section.from, to: section.to } });
      response.data.data.forEach(train => uniqueTrainNumbers.add(train.train_base.train_no));
    } catch (error) {
      console.error(`Could not fetch data for section ${section.description}: ${error.message}`);
    }
  }
  console.log(`Discovered ${uniqueTrainNumbers.size} unique trains.`);

  console.log(`\n--- PHASE 2: Processing ${uniqueTrainNumbers.size} Unique Trains ---`);
  for (const trainNo of uniqueTrainNumbers) {
    try {
      console.log(`--- Processing Train No: ${trainNo} ---`);
      
      const infoResponse = await axios.get(`${LOCAL_API_BASE_URL}/trains/getTrain`, { params: { trainNo } });
      const trainInfo = infoResponse.data.data;
      
      const routeResponse = await axios.get(`${LOCAL_API_BASE_URL}/trains/getRoute`, { params: { trainNo } });
      const trainRoute = routeResponse.data.data;
      
      if (!trainInfo || !trainInfo.train_name || !trainRoute || trainRoute.length === 0) {
        console.warn(`--> WARNING: Incomplete data received for train ${trainNo}. Skipping.`);
        continue;
      }
      
      const attributes = getTrainAttributes(trainInfo);

      await Train.create({
        train_id_string: `${trainNo}_${trainInfo.train_name.replace(/ /g, '_')}`,
        train_no: trainNo,
        train_name: trainInfo.train_name,
        train_type: attributes.train_type,
        priority: attributes.priority,
        source_stn_code: trainInfo.from_stn_code,
        dstn_stn_code: trainInfo.to_stn_code,
        running_days: trainInfo.running_days,
      });
      
      await Route.create({
        train_no: trainNo,
        train_name: trainInfo.train_name,
        source_stn_code: trainInfo.from_stn_code,
        dstn_stn_code: trainInfo.to_stn_code,
        priority: attributes.priority,
        stops: trainRoute,
      });
      console.log(`Successfully processed train ${trainNo}.`);

    } catch (error) {
      console.error(`--> ERROR: Failed to process train ${trainNo}. Error: ${error.message}`);
    }
  }

  await mongoose.disconnect();
  console.log('\n--- Database Seeding Finished ---');
};

seedDatabase().catch(err => {
  console.error('Seeding process failed with an error:', err);
  mongoose.disconnect();
});