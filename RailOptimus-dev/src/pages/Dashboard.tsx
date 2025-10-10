

// //&final

// /*import React, { useState, useEffect } from "react";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Badge } from "@/components/ui/badge";
// import { Button } from "@/components/ui/button";
// import { Alert as UIAlert, AlertDescription } from "@/components/ui/alert";
// import axios from "axios";
// import { useAuthStore } from "@/stores/authStore";
// import AIPredictorCard from "../components/AIPredictorCard"; // Adjust path if necessary
// import { 
//   Train, 
//   Clock, 
//   AlertTriangle, 
//   CheckCircle, 
//   XCircle,
//   Activity,
//   TrendingUp,
//   Loader2
// } from "lucide-react";
// import LiveScheduleView from "../components/Livescheduleview"; // Adjust path if necessary

// // --- Helper function to parse schedule time (Robust Version) ---
// // This function is now inside the dashboard component and handles both HH.mm and HH:mm formats.
// const parseScheduleTime = (day: string, timeStr: string): Date | null => {
//   if (!timeStr || timeStr === "First" || timeStr === "Last") return null;

//   // This line handles both "." and ":" as separators.
//   const formattedTime = timeStr.replace(':', '.');
//   const [hours, minutes] = formattedTime.split('.').map(Number);

//   if (isNaN(hours) || isNaN(minutes)) {
//     console.warn(`[Simulation] Could not parse time: ${timeStr}`);
//     return null;
//   }

//   const now = new Date();
//   // We treat "Day 1" as today, "Day 2" as tomorrow, etc., for the simulation.
//   const scheduledDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + (parseInt(day, 10) - 1), hours, minutes);
//   return scheduledDate;
// };
// // --- NEW: Helper function to determine train type based on priority ---
// const getTrainType = (priority: number): string => {
//     switch (priority) {
//         case 0:
//             return "Premium Express"; // For Rajdhani, Shatabdi, etc.
//         case 1:
//             return "Superfast/Express";
//         case 2:
//             return "Passenger/Local";
//         default:
//             return "Special"; // A sensible default for other priorities
//     }
// };



// export default function Dashboard() {
//   const { user } = useAuthStore();
//   const [currentTime, setCurrentTime] = useState(new Date());
//   const [allTrainRoutes, setAllTrainRoutes] = useState<any[]>([]); // This will hold the static schedule
//   const [liveTrainData, setLiveTrainData] = useState<any[]>([]); // This holds the calculated "live" trains
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   //--CHANGE: Step 2 - New state is added to keep track of the train the user clicks on.
//   const [selectedTrain, setSelectedTrain] = useState<any | null>(null);


//   // --- Step 1: Fetch the static schedule once ---
//   useEffect(() => {
//     const fetchTrainRoutes = async () => {
//       if (!user?.section) {
//         setLoading(false);
//         return;
//       }
//       try {
//         setLoading(true);
//         const section = user.section.toLowerCase();
//         const response = await axios.get(`http://localhost:5000/api/trains/${section}`);
//         setAllTrainRoutes(response.data);
//         setError(null);
//       } catch (err) {
//         console.error("Failed to fetch train routes:", err);
//         setError("Could not load train data for your section.");
//       } finally {
//         setLoading(false);
//       }
//     };
//     fetchTrainRoutes();
//   }, [user]);

//   // --- Step 2: Run the simulation on a timer in the frontend ---
//   useEffect(() => {
//     const simulationInterval = setInterval(() => {
//       const now = new Date();
//       setCurrentTime(now);

//       if (allTrainRoutes.length === 0) return
//       setLiveTrainData([]); // Clear previous data before recalculating
      
//       const activeTrains = allTrainRoutes.map((train) => {
//         const firstStop = train.stops[0];
//         const lastStop = train.stops[train.stops.length - 1];

//         const startTime = parseScheduleTime(firstStop.day, firstStop.depart);
//         const endTime = parseScheduleTime(lastStop.day, lastStop.arrive);

//         // This is the core logic that determines if a train is "running" right now.
//         const isActive = startTime && endTime && now >= startTime && now <= endTime;
//         //--CHANGE: The simulation logic was enhanced to calculate the train's current location.
//         let currentStop = firstStop;
//         for (const stop of train.stops) {
//             const arrivalTime = parseScheduleTime(stop.day, stop.arrive);
//             if (arrivalTime && now >= arrivalTime) {
//                 currentStop = stop;
//             } else {
//                 break;
//             }
//         }        
//         if (!isActive) return null; // If not active, discard it for now.
//         // --- NEW: lookup delay for this stop ---
//         const delayMinutes = Math.round(train.delays?.[currentStop.code] || 0); 
   


//         // Simulate a delay for realism // &Removed
//         // const delay =0;
//         // const status = "on-time";
//         // --- NEW: classify delay minutes into status ---

//         // This function now correctly defines all status levels for your 0-300+ minute data.
//         const getDelayStatus = (delayMins: number): string => {
//             if (delayMins <= 15) return "on-time";
//             if (delayMins <= 60) return "medium-delay";
//             if (delayMins <= 180) return "high-delay";
//             return "extreme-delay";
//         };

//          const status = getDelayStatus(delayMinutes);
        
//         const type = getTrainType(train.priority)

//         return { 
//           id: train.train_no, 
//           type: train.train_name, 
//           delay: delayMinutes, 
//           status: status
//         };
//       }).filter(Boolean);

//               // ✅ --- THIS IS THE MISSING LINE --- ✅
//       // Update the state to trigger a re-render with the new data.
//         setLiveTrainData(activeTrains as any[]);

//     }, 5000); // Reruns the calculation every 5 seconds

//     return () => clearInterval(simulationInterval); // Clean up the timer
//   }, [allTrainRoutes]); // Rerun this setup if the base schedule data changes


//   // --- CHANGE 2: UPDATED HELPER FUNCTIONS FOR STYLING ---
//   // These functions now recognize all the new status levels.
//   const getStatusColor = (status: string) => {
//     switch (status) {
//       case "on-time":
//         return "success";
//       case "medium-delay":
//         return "warning";
//       case "high-delay":
//         return "danger";
//       case "extreme-delay":
//         return "destructive";
//       default:
//         return "secondary";
//     }
//   };

//   const getStatusIcon = (status: string) => {
//     switch (status) {
//       case "on-time":
//         return <CheckCircle className="h-5 w-5 text-success" />;
//       case "medium-delay":
//         return <Clock className="h-5 w-5 text-warning" />;
//       case "high-delay":
//         return <XCircle className="h-5 w-5 text-danger" />;
//       case "extreme-delay":
//         return <AlertTriangle className="h-5 w-5 text-destructive" />;
//       default:
//         return <Activity className="h-5 w-5" />;
//     }
//   };
//   const getPriorityColor = (priority: string) => {
//     if (priority === "high") return "danger";
//     if (priority === "medium") return "warning";
//     return "secondary";
//   };

//   if (loading) {
//     return (
//         <div className="flex items-center justify-center h-full">
//             <Loader2 className="h-12 w-12 animate-spin text-primary" />
//             <p className="ml-4 text-lg">Loading Live Train Data...</p>
//         </div>
//     );
//   }

//   if (error) {
//     return (
//         <div className="flex items-center justify-center h-full">
//             <AlertTriangle className="h-12 w-12 text-danger" />
//             <p className="ml-4 text-lg text-danger">{error}</p>
//         </div>
//     );
//   }

// //& this is scrollable perfect
//   return (
//     <div className="space-y-6">
//         {/* Header */
//         {/*<div className="flex justify-between items-center">*/}
//             {/*<div>*/}
//         {/*//         <h1 className="text-3xl font-bold text-foreground">Control Dashboard</h1>
//         //         <p className="text-muted-foreground">
//         //             Real-time railway section monitoring and control
//         //         </p>
//         //     </div>
//         //     <div className="text-right">
//         //         <p className="text-sm text-muted-foreground">Current Time</p>
//         //         <p className="text-2xl font-mono font-bold text-foreground">
//         //             {currentTime.toLocaleTimeString()}
//         //         </p>
//         //     </div>
//         // </div>*/}


// {/* Stats Cards */}
// /*<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
//     <Card className="border-border shadow-soft">
//         <CardContent className="p-6 flex items-center justify-between">
//             <div>
//                 <p className="text-sm font-medium text-muted-foreground">Active Trains</p>
//                 <p className="text-2xl font-bold text-foreground">{liveTrainData.length}</p>
//             </div>
//             <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg">
//                 <Train className="h-6 w-6 text-primary" />
//             </div>
//         </CardContent>
//     </Card>
//     <Card className="border-border shadow-soft">
//         <CardContent className="p-6 flex items-center justify-between">
//             <div>
//                 <p className="text-sm font-medium text-muted-foreground">On Time</p>
//                 <p className="text-2xl font-bold text-success">
//                     {liveTrainData.filter(t => t.status === "on-time").length}
//                 </p>
//             </div>
//             <div className="flex items-center justify-center w-12 h-12 bg-success/10 rounded-lg">
//                 <CheckCircle className="h-6 w-6 text-success" />
//             </div>
//         </CardContent>
//     </Card>
//     <Card className="border-border shadow-soft">
//         <CardContent className="p-6 flex items-center justify-between">
//             <div>
//                 <p className="text-sm font-medium text-muted-foreground">Delayed</p>
//                 <p className="text-2xl font-bold text-warning">
//                     {liveTrainData.filter(t => t.delay > 0).length}
//                 </p>
//             </div>
//             <div className="flex items-center justify-center w-12 h-12 bg-warning/10 rounded-lg">
//                 <Clock className="h-6 w-6 text-warning" />
//             </div>
//         </CardContent>
//     </Card>
// </div>
//         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//             {/*<div className="lg:col-span-2">
//                 <Card className="border-border shadow-soft">
//                     <CardHeader>
//                         <CardTitle className="flex items-center gap-2">
//                             <Train className="h-5 w-5" />
//                             Live Train Tracking
//                         </CardTitle>
//                         <CardDescription>
//                             Real-time status of trains in your section
//                         </CardDescription>
//                     </CardHeader>
//                     <CardContent>
//                         --- CHANGE: Added a scrollable container ---
//                         This div now has a maximum height and will scroll vertically if the content overflows.
//                         <div className="relative max-h-[calc(100vh-450px)] overflow-y-auto pr-2">
//                             <div className="space-y-3">
//                                 {liveTrainData.length > 0 ? liveTrainData.map((train) => (
//                                     <div
//                                         key={train.id}
//                                         className="flex items-center justify-between p-4 border border-border rounded-lg bg-card hover:shadow-soft transition-shadow"
//                                     >
//                                         <div className="flex items-center gap-4">
//                                             <div className="flex items-center gap-2">
//                                                 {getStatusIcon(train.status)}
//                                                 <span className="font-semibold text-foreground">{train.id}</span>
//                                             </div>
//                                             <div>
//                                                 <p className="font-medium text-foreground">{train.type}</p>
//                                             </div>
//                                         </div>
//                                         <div className="text-right">
//                                             <Badge variant={getStatusColor(train.status) as any}>
//                                                 {train.delay === 0 ? "On Time" : `+${train.delay}m`}
//                                             </Badge>
//                                         </div>
//                                     </div>
//                                 )) : (
//                                     <div className="text-center py-8 text-muted-foreground">
//                                         <p>No active trains in this section at the moment.</p>
//                                     </div>
//                                 )}
//                             </div>
//                         </div>
//                     </CardContent>
//                 </Card>
//             </div>

//             <div className="grid grid-cols-1 md:grid-cols-1 lg:grid-cols-1 gap-6">
//                 <AIPredictorCard /> {/* Add the new component here */}
//                 {/* ... (other cards or components) ... */}
//             {/*</div>

//         </div>
//     </div>
//   );
// }*/}
import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { apiUrl } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import AIPredictorCard from "../components/AIPredictorCard";
import {
  Train,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  Activity,
  Loader2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

// --- Helpers ---
const parseScheduleTime = (day: string, timeStr: string): Date | null => {
  if (!timeStr || timeStr === "First" || timeStr === "Last") return null;
  const normalized = timeStr.replace(".", ":");
  const [hStr, mStr] = normalized.split(":");
  const hours = Number(hStr);
  const minutes = Number(mStr);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  const now = new Date();
  return new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() + (parseInt(day, 10) - 1),
    hours,
    minutes
  );
};

const getTrainType = (priority: number) => {
  switch (priority) {
    case 0:
      return "Premium Express";
    case 1:
      return "Superfast/Express";
    case 2:
      return "Passenger/Local";
    default:
      return "Special";
  }
};

// 🔴 CHANGED: delay status now hardcoded instead of using delay minutes
const getDelayStatus = (trainId: string) => {
  // Example logic: mark some trains as delayed, others on-time
  if (trainId.startsWith("12")) return "medium-delay"; // demo: delayed
  if (trainId.startsWith("14")) return "high-delay";   // demo: more delayed
  if(trainId.startsWith("20")) return "extreme-delay"; // demo: extremely delayed
  return "on-time"; // default
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "on-time":
      return "success";
    case "medium-delay":
      return "warning";
    case "high-delay":
      return "danger";
    case "extreme-delay":
      return "destructive";
    default:
      return "secondary";
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case "on-time":
      return <CheckCircle className="h-5 w-5 text-success" />;
    case "medium-delay":
      return <Clock className="h-5 w-5 text-warning" />;
    case "high-delay":
      return <XCircle className="h-5 w-5 text-danger" />;
    case "extreme-delay":
      return <AlertTriangle className="h-5 w-5 text-destructive" />;
    default:
      return <Activity className="h-5 w-5" />;
  }
};

// ---------------- Component ----------------
export default function Dashboard() {
  const { user } = useAuthStore();
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const [allTrainRoutes, setAllTrainRoutes] = useState<any[]>([]);
  const [liveTrainData, setLiveTrainData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTrain, setSelectedTrain] = useState<any | null>(null);

  // Fetch static schedule once
  useEffect(() => {
    const fetchTrainRoutes = async () => {
      if (!user?.section) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const section = user.section.toLowerCase();
        const resp = await axios.get(apiUrl(`/api/trains/${section}`));
        setAllTrainRoutes(resp.data || []);
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Could not load train data for your section.");
      } finally {
        setLoading(false);
      }
    };
    fetchTrainRoutes();
  }, [user]);

  // Simulation timer: compute active trains and currentStop
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setCurrentTime(now);
      if (!allTrainRoutes || allTrainRoutes.length === 0) {
        setLiveTrainData([]);
        return;
      }

      const active = allTrainRoutes
        .map((train: any) => {
          if (!train.stops || train.stops.length === 0) return null;

          const first = train.stops[0];
          const last = train.stops[train.stops.length - 1];
          const startTime = parseScheduleTime(first.day, first.depart);
          const endTime = parseScheduleTime(last.day, last.arrive);

          const isActive =
            startTime && endTime && now >= startTime && now <= endTime;
          if (!isActive) return null;

          // Determine currentStop
          let currentStop = first;
          for (const stop of train.stops) {
            const arr = parseScheduleTime(stop.day, stop.arrive);
            const dep = parseScheduleTime(stop.day, stop.depart);
            if (arr && now >= arr) {
              currentStop = stop;
            }
            if (dep && now >= dep) {
              currentStop = stop;
            }
          }

          // 🔴 CHANGED: use hardcoded delay status, ignore delayMinutes
          const status = getDelayStatus(train.train_no);
          const type = getTrainType(train.priority);

          return {
            id: train.train_no,
            train_name: train.train_name,
            stops: train.stops,
            currentStop,
            type,
            delay: status === "on-time" ? 0 : 1, // 🔴 dummy delay shown
            status,
          };
        })
        .filter(Boolean);

      setLiveTrainData(active as any[]);
    };

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [allTrainRoutes]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="ml-4 text-lg">Loading Live Train Data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <AlertTriangle className="h-12 w-12 text-danger" />
        <p className="ml-4 text-lg text-danger">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Control Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time railway section monitoring and control
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-muted-foreground">Current Time</p>
          <p className="text-2xl font-mono font-bold">
            {currentTime.toLocaleTimeString()}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-border shadow-soft">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Active Trains
              </p>
              <p className="text-2xl font-bold text-foreground">
                {liveTrainData.length}
              </p>
            </div>
            <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg">
              <Train className="h-6 w-6 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-soft">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">On Time</p>
              <p className="text-2xl font-bold text-success">
                {liveTrainData.filter((t) => t.status === "on-time").length}
              </p>
            </div>
            <div className="flex items-center justify-center w-12 h-12 bg-success/10 rounded-lg">
              <CheckCircle className="h-6 w-6 text-success" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-soft">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Delayed</p>
              <p className="text-2xl font-bold text-warning">
                {liveTrainData.filter((t) => t.status !== "on-time").length}
              </p>
            </div>
            <div className="flex items-center justify-center w-12 h-12 bg-warning/10 rounded-lg">
              <Clock className="h-6 w-6 text-warning" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live train list */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Train className="h-5 w-5" /> Live Train Tracking
              </CardTitle>
              <CardDescription>
                Real-time status of trains in your section
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative max-h-[calc(100vh-450px)] overflow-y-auto pr-2">
                <div className="space-y-3">
                  {liveTrainData.length > 0 ? (
                    liveTrainData.map((train) => (
                      <div
                        key={train.id}
                        onClick={() => setSelectedTrain(train)}
                        className="flex items-center justify-between p-4 border border-border rounded-lg bg-card hover:shadow-soft transition-shadow cursor-pointer"
                      >
                        <div className="flex items-center gap-4">
                          {getStatusIcon(train.status)}
                          <div>
                            <p className="font-semibold">{train.id}</p>
                            <p className="text-sm text-muted-foreground">
                              {train.train_name}
                            </p>
                          </div>
                        </div>
                        <Badge variant={getStatusColor(train.status) as any}>
                          {train.status === "on-time"
                            ? "On Time"
                            : train.status.replace("-", " ")}
                        </Badge>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>No active trains in this section at the moment.</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="grid grid-cols-1 gap-6">
          <AIPredictorCard />
        </div>
      </div>

      {/* Modal showing full schedule on click */}
      <Dialog
        open={!!selectedTrain}
        onOpenChange={(open) => {
          if (!open) setSelectedTrain(null);
        }}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Train {selectedTrain?.id} — {selectedTrain?.train_name}
            </DialogTitle>
            <DialogDescription>
              Full schedule (green = passed, blue = current, gray = upcoming)
            </DialogDescription>
          </DialogHeader>

          {selectedTrain && (() => {
            const now = new Date();

            return (
              <div className="space-y-2 mt-4">
                {selectedTrain.stops.map((stop: any, idx: number) => {
                  const arrival = parseScheduleTime(stop.day, stop.arrive);
                  const depart = parseScheduleTime(stop.day, stop.depart);

                  let status: "past" | "current" | "future" = "future";
                  if (depart && now > depart) {
                    status = "past";
                  } else if (
                    (arrival && now >= arrival && (!depart || now <= depart)) ||
                    (depart && now >= depart && idx === selectedTrain.stops.length - 1)
                  ) {
                    status = "current";
                  }

                  const bgColor =
                    status === "past"
                      ? "bg-green-50 border-green-200"
                      : status === "current"
                      ? "bg-blue-50 border-blue-300"
                      : "bg-gray-50 border-border";

                  const stopName =
                    stop.source_stn_name ||
                    stop.name ||
                    stop.station_name ||
                    stop.fullname ||
                    stop.code;

                  return (
                    <div
                      key={stop.code + idx}
                      className={`flex items-center justify-between p-3 rounded border ${bgColor}`}
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{stopName}</span>
                          <span className="text-xs text-muted-foreground">
                            ({stop.source_stn_code || stop.code})
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Arrive: {stop.arrive ?? "-"} • Depart:{" "}
                          {stop.depart ?? "-"}
                        </div>
                      </div>
                      <div className="text-right">
                        {status === "past" && (
                          <span className="text-sm text-green-600">ARRIVED</span>
                        )}
                        {status === "current" && (
                          <span className="text-sm text-blue-600 font-semibold">
                            CURRENT
                          </span>
                        )}
                        {status === "future" && (
                          <span className="text-sm text-gray-400">UPCOMING</span>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div className="flex justify-end mt-4">
                  <Button onClick={() => setSelectedTrain(null)}>Close</Button>
                </div>
              </div>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
}

