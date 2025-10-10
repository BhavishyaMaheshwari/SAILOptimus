import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Train, MapPin } from "lucide-react";

// This is the dedicated component for the live schedule view.
const LiveScheduleView = ({ train, onBack }) => {
    // --- FIX: Add a safety check before rendering ---
    // If the train data is incomplete (e.g., missing stops), show an error message instead of crashing.
    if (!train || !train.stops || train.stops.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Error</CardTitle>
                    <CardDescription>Could not display schedule. The train data is incomplete.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Button onClick={onBack} variant="outline"> &larr; Back to Dashboard</Button>
                </CardContent>
            </Card>
        );
    }

    // --- FIX: Use optional chaining for safer access to properties ---
    // This prevents errors if a specific stop is malformed.
    const startStation = train.stops[0]?.source_stn_name || 'Unknown';
    const endStation = train.stops[train.stops.length - 1]?.source_stn_name || 'Unknown';

    return (
        <Card className="border-border shadow-soft">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="flex items-center gap-3">
                            <Train className="h-6 w-6" />
                            Live Schedule: Train {train.train_no}
                        </CardTitle>
                        <CardDescription>{train.type} - {startStation} to {endStation}</CardDescription>
                    </div>
                    <Button onClick={onBack} variant="outline"> &larr; Back to Dashboard</Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="border rounded-lg overflow-hidden">
                    {/* Header for the schedule table */}
                    <div className="grid grid-cols-5 bg-muted/50 font-semibold text-sm p-2 border-b">
                        <div>Station</div>
                        <div className="text-center">Arrival</div>
                        <div className="text-center">Departure</div>
                        <div className="text-center">Day</div>
                        <div className="text-right">Zone</div>
                    </div>
                    {/* Scrollable body of the schedule table */}
                    <div className="max-h-[60vh] overflow-y-auto">
                        {train.stops.map((stop, index) => {
                            const isCurrent = stop.source_stn_code === train.currentStopCode;
                            return (
                                <div 
                                    key={index}
                                    className={`grid grid-cols-5 p-3 text-sm border-b last:border-b-0 transition-colors ${isCurrent ? 'bg-primary/10 text-primary-foreground font-semibold' : 'hover:bg-muted'}`}
                                >
                                    <div className="flex items-center gap-2">
                                        {isCurrent && <MapPin className="h-4 w-4 text-primary animate-pulse" />}
                                        <span>{stop.source_stn_name} ({stop.source_stn_code})</span>
                                    </div>
                                    <div className="text-center">{stop.arrive}</div>
                                    <div className="text-center">{stop.depart}</div>
                                    <div className="text-center">{stop.day}</div>
                                    <div className="text-right">{stop.zone}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default LiveScheduleView;

