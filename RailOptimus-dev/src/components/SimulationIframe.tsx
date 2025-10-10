import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, ExternalLink, RefreshCw, AlertCircle } from "lucide-react";

interface SimulationIframeProps {
  className?: string;
}

const SimulationIframe: React.FC<SimulationIframeProps> = ({ className }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);

  const SIMULATION_URL = "http://localhost:8050";

  const handleIframeLoad = () => {
    setIsLoading(false);
    setIsError(false);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setIsError(true);
  };

  const refreshSimulation = () => {
    setIsLoading(true);
    setIsError(false);
    setIframeKey(prev => prev + 1);
  };

  const openInNewTab = () => {
    window.open(SIMULATION_URL, '_blank');
  };

  return (
    <div className={className}>
      <Card className="h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle className="flex items-center gap-2">
            <span>Railway Simulation - RailOptiSim</span>
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          </CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={refreshSimulation}
              disabled={isLoading}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={openInNewTab}
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Open in New Tab
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isError ? (
            <Alert className="m-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex flex-col gap-2">
                <span>
                  Failed to load RailOptiSim. Please ensure the Python simulation is running on port 8050.
                </span>
                <div className="flex gap-2">
                  <Button size="sm" onClick={refreshSimulation}>
                    Retry
                  </Button>
                  <Button size="sm" variant="outline" onClick={openInNewTab}>
                    Open Directly
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          ) : (
            <div className="relative">
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
                  <div className="flex flex-col items-center gap-2">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <p className="text-sm text-muted-foreground">Loading RailOptiSim...</p>
                  </div>
                </div>
              )}
              <iframe
                key={iframeKey}
                src={SIMULATION_URL}
                title="RailOptiSim Railway Simulation"
                width="100%"
                height="800px"
                style={{
                  border: 'none',
                  borderRadius: '0 0 8px 8px',
                  minHeight: '800px'
                }}
                onLoad={handleIframeLoad}
                onError={handleIframeError}
                allow="fullscreen"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SimulationIframe;