import React, { useState, useMemo, useEffect, useRef } from 'react';

// --- Part 1: Configuration for MarineTraffic Port Maps ---
const portCoordinates = {
  haldia: { lat: 22.05, lon: 88.06 },
  paradip: { lat: 20.26, lon: 86.67 },
  kolkata: { lat: 22.57, lon: 88.36 },
  chennai: { lat: 13.08, lon: 80.27 },
  visakhapatnam: { lat: 17.68, lon: 83.21 },
};
type PortName = keyof typeof portCoordinates;


// --- Part 2: Helper Component for VesselFinder (Handles document.write) ---
const VesselFinderMap: React.FC<{ params: Record<string, any> }> = ({ params }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe || Object.keys(params).length === 0) return;

    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!iframeDoc) return;

    // Create the HTML content for the iframe, including the script variables
    const mapHtml = `
      <html>
        <head><style>body { margin: 0; padding: 0; }</style></head>
        <body>
          <script>
            ${Object.entries(params).map(([key, value]) => `var ${key}=${JSON.stringify(value)};`).join('\n')}
          </script>
          <script src="https://www.vesselfinder.com/aismap.js"></script>
        </body>
      </html>
    `;

    // Write this HTML into the iframe to correctly handle the script
    iframeDoc.open();
    iframeDoc.write(mapHtml);
    iframeDoc.close();
  }, [params]);

  return (
    <div style={{ border: '1px solid #ccc', borderRadius: '8px', overflow: 'hidden', lineHeight: 0 }}>
      <iframe
        ref={iframeRef}
        title="Vessel Finder IMO Tracker"
        style={{ width: '100%', height: '400px', border: 'none' }}
        scrolling="no"
      />
    </div>
  );
};


// --- Main Page Component Combining Both Features ---
const MapPage: React.FC = () => {
  // State for MarineTraffic Port Maps
  const [selectedPort, setSelectedPort] = useState<PortName>('haldia');

  // State for VesselFinder IMO Tracker
  const [imoInput, setImoInput] = useState<string>('');
  const [trackedImo, setTrackedImo] = useState<string>('9506291'); // Default example ship
  const [shipTrackParams, setShipTrackParams] = useState({});

  // URL for the MarineTraffic iframe
  const marineTrafficEmbedUrl = useMemo(() => {
    const port = portCoordinates[selectedPort];
    return `https://www.marinetraffic.com/en/ais/embed/zoom:10/centery:${port.lat}/centerx:${port.lon}/maptype:3/shownames:true`;
  }, [selectedPort]);
  
  // Parameters for the VesselFinder iframe
  useEffect(() => {
    if (trackedImo) {
      setShipTrackParams({
        width: "100%",
        height: "400",
        names: true,
        imo: trackedImo,
        show_track: true,
      });
    }
  }, [trackedImo]);

  const handleTrackShip = () => {
    if (imoInput.trim()) {
      setTrackedImo(imoInput.trim());
    }
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', backgroundColor: '#f4f7f6' }}>
      
      {/* --- Section 1: MarineTraffic Port Maps --- */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', borderBottom: '2px solid #005f73', paddingBottom: '0.5rem' }}>Vessel Activity at Major Indian Ports</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', margin: '1rem 0' }}>
          {Object.keys(portCoordinates).map((portName) => (
            <button key={portName} onClick={() => setSelectedPort(portName as PortName)}>
              {portName.charAt(0).toUpperCase() + portName.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ border: '1px solid #ccc', borderRadius: '8px', overflow: 'hidden', lineHeight: 0 }}>
            <iframe
                key={selectedPort}
                src={marineTrafficEmbedUrl}
                title={`Map of ${selectedPort}`}
                style={{ width: '100%', height: '500px', border: 'none' }}
            />
        </div>
      </div>

      <hr style={{margin: '2rem 0', borderTop: '1px solid #ddd'}} />

      {/* --- Section 2: VesselFinder IMO Tracker --- */}
      <div style={{ marginTop: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', borderBottom: '2px solid #005f73', paddingBottom: '0.5rem' }}>Track a Single Vessel by IMO (via VesselFinder)</h2>
        <div style={{ display: 'flex', gap: '10px', margin: '1rem 0' }}>
          <input
            type="text"
            value={imoInput}
            onChange={(e) => setImoInput(e.target.value)}
            placeholder="Enter IMO number"
            style={{ padding: '10px', fontSize: '1rem', flexGrow: 1 }}
          />
          <button onClick={handleTrackShip} style={{ padding: '10px 20px', cursor: 'pointer' }}>
            Track Ship
          </button>
        </div>
        <VesselFinderMap params={shipTrackParams} />
      </div>

    </div>
  );
};

export default MapPage;