import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
// fix for ES modules __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// const fs = require('fs');
// const path = require('path');

// This function will be called by the route we just created.
export const getMapDataBySection = (req, res) => {
  // 1. Get the section name from the URL parameters.
  const section = req.params.section.toLowerCase(); // Normalize to lowercase
    if (!section) {
    return res.status(400).json({ message: 'Section parameter is missing.' });
  }
  const mapFilePath = path.join(__dirname, '..', 'maps', 'mapdata', `${section}.geojson`);
  console.log(`[Backend] Searching for map file at: ${mapFilePath}`);
  // Basic validation to prevent directory traversal attacks
  

  
  // 2. Construct the full path to the requested geojson file.
  // path.join is used to create a safe, cross-platform file path.
  // '__dirname, '..'` goes up one level from /controllers to the project root.

    // --- NEW LOGIC: Read the file first before sending ---
  // fs.readFile(mapFilePath, 'utf8', (err, data) => {
  //   if (err) {
  //     console.error(`[Backend] ERROR reading the file:`, err);
  //     return res.status(500).json({ message: "Failed to read map file." });
  //   }


  // 3. Check if the file exists.
  // fs.access(mapFilePath, fs.constants.F_OK, (err) => {
  //   if (err) {
  //     // If the file doesn't exist, send a 404 Not Found error.
  //     console.warn(`Map file not found for section '${section}' at: ${mapFilePath}`);
  //     return res.status(404).json({ message: `Map data not found for section: ${section}` });
  //   }
  fs.readFile(mapFilePath, 'utf8', (err, data) => {
    if (err) {
      // If ANY error happens (file not found, permissions error, etc.)
      // we handle it here.
      console.error(`[Backend] ERROR: Could not read file for section '${section}'.`, err);
      return res.status(404).json({ message: "..." });
    }
    // If there was no error, we proceed.
    console.log(`[Backend] Successfully read file for '${section}'. Sending data.`);
    res.status(200).json(JSON.parse(data));
  });
    // 4. If the file exists, send it back as the response.
    // res.sendFile(mapFilePath);

};
