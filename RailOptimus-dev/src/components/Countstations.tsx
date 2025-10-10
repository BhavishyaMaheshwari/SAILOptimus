import React, { useState, useEffect } from 'react';

const DataSummary: React.FC = () => {
  // State to hold the counts. Initialized to a loading message.
  const [trackCount, setTrackCount] = useState<number | string>('Loading...');
  const [stationCount, setStationCount] = useState<number | string>('Loading...');

  useEffect(() => {
    // Function to fetch and process the GeoJSON data
    const fetchAndCountFeatures = async () => {
      try {
        // Fetch the file from the public folder
        const response = await fetch('/data.geojson');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const geojsonData = await response.json();

        let tracks = 0;
        let stations = 0;

        // Loop through each feature to count them
        for (const feature of geojsonData.features) {
          const geometryType = feature?.geometry?.type;

          if (geometryType === 'LineString') {
            tracks++; // This is a track
          } else if (geometryType === 'Point') {
            stations++; // This is a station
          }
        }

        // Update the state with the final counts
        setTrackCount(tracks);
        setStationCount(stations);

      } catch (error) {
        console.error("Failed to fetch or parse GeoJSON:", error);
        setTrackCount('Error');
        setStationCount('Error');
      }
    };

    fetchAndCountFeatures();
  }, []); // The empty array ensures this runs only once when the component mounts

  return (
    <div>
      <p><b>Tracks:</b> {trackCount}</p>
      <p><b>Stations:</b> {stationCount}</p>
    </div>
  );
};

export default DataSummary;