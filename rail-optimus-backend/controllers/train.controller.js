import mongoose from 'mongoose';

// This is the main function that will be called by our route.
export const getTrainsBySection = async (req, res) => {
  try {
    // 1. Get the section name from the URL parameters (e.g., 'agra', 'assam').
    const section = req.params.section;
    if (!section) {
      return res.status(400).json({ message: "Section parameter is required." });
    }

    // 2. Construct the dynamic collection name based on the section, adding an 's'.
    // This now creates names like "routeagras", "routeassams", etc.
    const collectionName = `route${section}s`;
    console.log(`[Backend] Attempting to fetch data from collection: ${collectionName}`);

    // 3. Access the collection dynamically and fetch all documents.
    // This is the standard Mongoose way to query a collection whose name you don't know in advance.
    const trains = await mongoose.connection.db.collection(collectionName).find({}).toArray();

    // 4. Check if any data was found.
    if (!trains || trains.length === 0) {
      console.warn(`[Backend] No trains found in collection: ${collectionName}`);
      return res.status(404).json({ message: `No train data found for section: ${section}` });
    }
    
    // 5. If successful, send the array of trains back to the frontend.
    console.log(`[Backend] Successfully fetched ${trains.length} trains from ${collectionName}.`);
    res.status(200).json(trains);

  } catch (error) {
    // If any other error occurs (e.g., database connection issue), handle it here.
    console.error("Error fetching dynamic train data from MongoDB:", error);
    res.status(500).json({ message: "An error occurred on the server while fetching train data." });
  }
};
