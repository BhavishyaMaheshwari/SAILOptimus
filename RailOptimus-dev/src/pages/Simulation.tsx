import React from "react";
import SimulationIframe from "@/components/SimulationIframe";

export default function Simulation() {
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Railway Simulation</h1>
        <p className="text-muted-foreground mt-2">
          Interactive railway network simulation and optimization platform
        </p>
      </div>
      
      <SimulationIframe className="w-full" />
    </div>
  );
}
