// // src/components/AIPredictorCard.tsx

// import { useState } from "react";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import { Button } from "@/components/ui/button";
// import { Separator } from "@/components/ui/separator";
// import { AlertTriangle, Clock } from "lucide-react";
// import axios from 'axios';
// import { useToast } from "@/hooks/use-toast";

// interface PredictionResult {
//     train: string;
//     city: string;
//     weather: string;
//     visibility: string;
//     predictedDelay: string;
//     probability: string;
// }

// const API_URL = 'http://localhost:5000/api'; // Make sure this URL is correct

// export default function AIPredictorCard() {
//     const [trains, setTrains] = useState("");
//     const [cities, setCities] = useState("");
//     const [currentSpeed, setCurrentSpeed] = useState("");
//     const [prediction, setPrediction] = useState<PredictionResult | null>(null);
//     const [isLoading, setIsLoading] = useState(false);
//     const { toast } = useToast();

//     const handlePredict = async () => {
//         setIsLoading(true);
//         setPrediction(null);
//         toast({ title: "Prediction in progress...", description: "Fetching results from the AI model." });

//         try {
//             const response = await axios.post(`${API_URL}/predict`, {
//                 trains,
//                 cities,
//                 currentSpeed: parseInt(currentSpeed),
//             });

//             if (response.data.status === 'success') {
//                 setPrediction(response.data.prediction);
//                 toast({ title: "Prediction Complete!", description: "Results are ready." });
//             }
//         } catch (err: any) {
//             console.error("Prediction failed:", err.response?.data?.message || err.message);
//             toast({
//                 title: "Prediction Failed",
//                 description: err.response?.data?.message || "An error occurred. Please try again.",
//                 variant: "destructive"
//             });
//         } finally {
//             setIsLoading(false);
//         }
//     };

//     return (
//         <Card className="border-border shadow-soft">
//             <CardHeader>
//                 <CardTitle className="flex items-center gap-5">
//                     <AlertTriangle className="h-10 w-10" />
//                     AI Delay Predictor
//                 </CardTitle>
//             </CardHeader>
//             <CardContent className="space-y-6">
//                 <div className="space-y-4">
//                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//                         <div className="space-y-2">
//                             <Label htmlFor="trains">Trains (e.g., 12951, 12952)</Label>
//                             <Input
//                                 id="trains"
//                                 placeholder="e.g., 12951:NDLS, 12952:MB"
//                                 value={trains}
//                                 onChange={(e) => setTrains(e.target.value)}
//                             />
//                         </div>
//                         <div className="space-y-2">
//                             <Label htmlFor="cities">City(s) for weather</Label>
//                             <Input
//                                 id="cities"
//                                 placeholder="e.g., Delhi, Mumbai"
//                                 value={cities}
//                                 onChange={(e) => setCities(e.target.value)}
//                             />
//                         </div>
//                     </div>
//                     <div className="space-y-2">
//                         <Label htmlFor="speed">Current Speed (km/h)</Label>
//                         <Input
//                             id="speed"
//                             type="number"
//                             placeholder="e.g., 80"
//                             value={currentSpeed}
//                             onChange={(e) => setCurrentSpeed(e.target.value)}
//                         />
//                     </div>
//                     <Button onClick={handlePredict} disabled={isLoading} className="w-full">
//                         {isLoading ? "Predicting..." : "Predict and Decide"}
//                     </Button>
//                 </div>
                
//                 {prediction && (
//                     <div className="space-y-4">
//                         <Separator />
//                         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//                             <div className="space-y-1">
//                                 <p className="text-sm font-medium text-muted-foreground">Train</p>
//                                 <p className="font-bold">{prediction.train}</p>
//                             </div>
//                             <div className="space-y-1">
//                                 <p className="text-sm font-medium text-muted-foreground">City & Weather</p>
//                                 <p className="font-bold">{prediction.city} ({prediction.weather})</p>
//                             </div>
//                             <div className="space-y-1">
//                                 <p className="text-sm font-medium text-muted-foreground">Visibility</p>
//                                 <p className="font-bold">{prediction.visibility}</p>
//                             </div>
//                             <div className="space-y-1">
//                                 <p className="text-sm font-medium text-muted-foreground">Current Speed</p>
//                                 <p className="font-bold">{currentSpeed} km/h</p>
//                             </div>
//                         </div>
//                         <Separator />
//                         <div className="space-y-2">
//                             <p className="text-lg font-semibold flex items-center gap-2">
//                                 <Clock className="h-5 w-5 text-warning" />
//                                 Predicted Delay
//                             </p>
//                             <p className="text-3xl font-bold text-warning">{prediction.predictedDelay}</p>
//                         </div>
//                         <div className="space-y-2">
//                             <p className="text-lg font-semibold">Probability</p>
//                             <p className="text-xl font-bold">{prediction.probability}</p>
//                         </div>
//                     </div>
//                 )}
//             </CardContent>
//         </Card>
//     );
// }


//&yyy
// import { useState } from "react";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import { Button } from "@/components/ui/button";
// import { Separator } from "@/components/ui/separator";
// import { AlertTriangle, Clock, ServerCrash, Train } from "lucide-react";
// import axios from 'axios';
// import { useToast } from "@/hooks/use-toast";

// // Updated interface to match the backend response
// interface PredictionResult {
//     train: string;
//     city?: string;
//     weather?: string;
//     visibility?: string;
//     predictedDelay?: string;
//     probabilities?: string;
//     currentSpeed?: string;
//     action?: string;
//     error?: string; // To handle prediction errors for a specific train
// }

// // Ensure your API URL is correct
// const API_URL = 'http://localhost:5000';

// export default function AIPredictorCard() {
//     const [trains, setTrains] = useState("12951:NDLS, 12952:BCT");
//     const [cities, setCities] = useState("Delhi, Mumbai");
//     const [speeds, setSpeeds] = useState("80, 75");
//     const [predictions, setPredictions] = useState<PredictionResult[] | null>(null);
//     const [isLoading, setIsLoading] = useState(false);
//     const { toast } = useToast();

//     const handlePredict = async () => {
//         setIsLoading(true);
//         setPredictions(null);
//         toast({ title: "Prediction in progress...", description: "Fetching results from the AI model." });

//         try {
//             // The request body now sends 'speeds'
//             const response = await axios.post(`${API_URL}/api/predict`, {
//                 trains,
//                 cities,
//                 speeds,
//             });

//             if (response.data.status === 'success') {
//                 setPredictions(response.data.predictions);
//                 toast({ title: "Prediction Complete!", description: "Results are ready." });
//             } else {
//                  toast({
//                     title: "Prediction Error",
//                     description: response.data.message || "An unknown error occurred.",
//                     variant: "destructive"
//                 });
//             }
//         } catch (err: any) {
//             console.error("Prediction failed:", err.response?.data?.message || err.message);
//             toast({
//                 title: "Prediction Failed",
//                 description: err.response?.data?.message || "Could not connect to the server. Is it running?",
//                 variant: "destructive"
//             });
//         } finally {
//             setIsLoading(false);
//         }
//     };

//     return (
//         <Card className="border-border shadow-soft w-full max-w-4xl mx-auto">
//             <CardHeader>
//                 <CardTitle className="flex items-center gap-3 text-2xl">
//                     <AlertTriangle className="h-8 w-8 text-primary" />
//                     AI Train Delay Predictor & Decision System
//                 </CardTitle>
//             </CardHeader>
//             <CardContent className="space-y-6">
//                 <div className="space-y-4">
//                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//                         <div className="space-y-2">
//                             <Label htmlFor="trains">Train(s) (e.g., 12951:NDLS)</Label>
//                             <Input
//                                 id="trains"
//                                 placeholder="e.g., 12951:NDLS, 12952:BCT"
//                                 value={trains}
//                                 onChange={(e) => setTrains(e.target.value)}
//                             />
//                         </div>
//                         <div className="space-y-2">
//                             <Label htmlFor="cities">City(s) for Weather (Optional)</Label>
//                             <Input
//                                 id="cities"
//                                 placeholder="e.g., Delhi, Mumbai"
//                                 value={cities}
//                                 onChange={(e) => setCities(e.target.value)}
//                             />
//                         </div>
//                     </div>
//                     <div className="space-y-2">
//                         <Label htmlFor="speeds">Speed(s) km/h (Optional)</Label>
//                         <Input
//                             id="speeds"
//                             placeholder="e.g., 80, 75"
//                             value={speeds}
//                             onChange={(e) => setSpeeds(e.target.value)}
//                         />
//                     </div>
//                     <Button onClick={handlePredict} disabled={isLoading} className="w-full text-lg py-6">
//                         {isLoading ? "Analyzing..." : "Predict and Decide"}
//                     </Button>
//                 </div>
                
//                 {predictions && (
//                     <div className="space-y-4 pt-4">
//                         <Separator />
//                         <h3 className="text-xl font-semibold">Prediction Results</h3>
//                         <div className="space-y-4">
//                             {predictions.map((p, index) => (
//                                 <div key={index} className="border p-4 rounded-lg bg-muted/40">
//                                     <p className="text-lg font-bold flex items-center gap-2 mb-3">
//                                        <Train className="h-5 w-5" /> {p.train}
//                                     </p>
//                                     {p.error ? (
//                                         <div className="text-destructive flex items-center gap-2">
//                                             <ServerCrash className="h-5 w-5" />
//                                             <span>Prediction Error: {p.error}</span>
//                                         </div>
//                                     ) : (
//                                         <>
//                                             <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
//                                                 <InfoItem label="City & Weather" value={`${p.city} (${p.weather})`} />
//                                                 <InfoItem label="Visibility" value={p.visibility} />
//                                                 <InfoItem label="Current Speed" value={p.currentSpeed} />
//                                                 <InfoItem label="Probabilities" value={p.probabilities} />
//                                             </div>
//                                             <Separator className="my-3"/>
//                                             <div className="flex flex-wrap items-center justify-between gap-4">
//                                                  <div className="space-y-1">
//                                                     <p className="text-sm font-semibold flex items-center gap-2 text-amber-600">
//                                                         <Clock className="h-4 w-4" />
//                                                         Predicted Delay
//                                                     </p>
//                                                     <p className="text-2xl font-bold text-amber-600">{p.predictedDelay}</p>
//                                                 </div>
//                                                  <div className="space-y-1 text-right">
//                                                     <p className="text-sm font-semibold">RL Action</p>
//                                                     <p className="text-xl font-bold text-primary">{p.action}</p>
//                                                 </div>
//                                             </div>
//                                         </>
//                                     )}
//                                 </div>
//                             ))}
//                         </div>
//                     </div>
//                 )}
//             </CardContent>
//         </Card>
//     );
// }

// // Helper component for displaying info items
// const InfoItem = ({ label, value }: { label: string, value: string | undefined }) => (
//     <div className="space-y-1">
//         <p className="text-xs font-medium text-muted-foreground">{label}</p>
//         <p className="font-semibold">{value || "N/A"}</p>
//     </div>
// );


import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { AlertTriangle, Clock, Cloud, Eye, TrainFront, Wind } from "lucide-react";
import axios from 'axios';
import { useToast } from "@/hooks/use-toast";

// Interface to define the structure of a single prediction result from the backend
interface PredictionResult {
    train: string;
    city: string;
    weather: string;
    visibility: string;
    predictedDelay: string;
    probabilities: string;
    currentSpeed: string;
    action: string;
    error?: string; // Optional field to hold error messages for a specific train
}

export default function AIPredictorCard() {
    const [trains, setTrains] = useState("12951:NDLS,12952:MB");
    const [cities, setCities] = useState("Delhi,Mumbai");
    const [speeds, setSpeeds] = useState("80,60");
    const [predictions, setPredictions] = useState<PredictionResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();

    const handlePredict = async () => {
        setIsLoading(true);
        setPredictions([]);
        toast({ title: "Prediction in progress...", description: "Fetching results from the AI model." });

        try {
            // Send the request to the backend. The URL is hardcoded to prevent 404 errors.
            const response = await axios.post('http://localhost:5001/api/predict', {
                trains,
                cities,
                speeds,
            });

            if (response.data.status === 'success') {
                setPredictions(response.data.predictions);
                toast({ title: "Prediction Complete!", description: "Results are ready." });
            } else {
                // Handle cases where the server returns a non-success status
                toast({
                    title: "Prediction Failed",
                    description: response.data.message || "An unexpected error occurred on the server.",
                    variant: "destructive"
                });
            }
        } catch (err: any) {
            console.error("Prediction failed:", err.response?.data?.message || err.message);
            toast({
                title: "Prediction Failed",
                description: err.response?.data?.message || "Could not connect to the server. Please ensure it's running.",
                variant: "destructive"
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card className="border-border shadow-soft w-full max-w-3xl mx-auto">
            <CardHeader>
                <CardTitle className="flex items-center gap-4">
                    <TrainFront className="h-10 w-10 text-primary" />
                    <span className="text-2xl font-bold">AI Delay Predictor & Decision System</span>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="p-4 border rounded-lg bg-muted/30 space-y-4">
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="trains">Train(s) (e.g., 12951:NDLS)</Label>
                            <Input
                                id="trains"
                                placeholder="e.g., 12951:NDLS, 12952:MB"
                                value={trains}
                                onChange={(e) => setTrains(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="cities">City(s) for weather</Label>
                            <Input
                                id="cities"
                                placeholder="e.g., Delhi, Mumbai"
                                value={cities}
                                onChange={(e) => setCities(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="speed">Speed(s) (km/h)</Label>
                        <Input
                            id="speed"
                            placeholder="e.g., 80, 60"
                            value={speeds}
                            onChange={(e) => setSpeeds(e.target.value)}
                        />
                    </div>
                    <Button onClick={handlePredict} disabled={isLoading} className="w-full">
                        {isLoading ? "Predicting..." : "Predict and Decide"}
                    </Button>
                </div>
                
                {predictions.length > 0 && (
                    <div className="space-y-4">
                        <Separator />
                        <h3 className="text-xl font-semibold text-center">Prediction Results</h3>
                        {predictions.map((p, index) => (
                            <div key={index} className="p-4 border rounded-lg space-y-3 bg-muted/50 transition-all">
                                <p className="font-bold text-lg text-primary flex items-center gap-2">
                                    <TrainFront className="h-5 w-5" />
                                    Results for Train: {p.train}
                                </p>
                                {p.error ? (
                                    <div className="text-destructive font-medium p-2 bg-destructive/10 rounded-md">
                                        <p>Could not generate prediction: {p.error}</p>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div className="space-y-3">
                                            <p className="flex items-center gap-2"><Cloud className="h-5 w-5 text-muted-foreground" /> <strong>Weather:</strong> {p.city} ({p.weather})</p>
                                            <p className="flex items-center gap-2"><Eye className="h-5 w-5 text-muted-foreground" /> <strong>Visibility:</strong> {p.visibility}</p>
                                            <p className="flex items-center gap-2"><Wind className="h-5 w-5 text-muted-foreground" /> <strong>Speed:</strong> {p.currentSpeed}</p>
                                        </div>
                                        <div className="space-y-3 p-3 bg-background rounded-md">
                                             <div className="flex items-center gap-2">
                                                <Clock className="h-5 w-5 text-warning" />
                                                <p className="font-semibold">Predicted Delay:</p>
                                                <p className="text-xl font-bold text-warning">{p.predictedDelay}</p>
                                            </div>
                                            <div>
                                                <p className="font-semibold">Delay Probabilities:</p>
                                                <p className="text-sm text-muted-foreground">{p.probabilities}</p>
                                            </div>
                                             <div className="p-3 bg-primary/10 rounded-md mt-2">
                                                <p className="font-semibold text-primary">Suggested Action (RL):</p>
                                                <p className="font-bold text-lg text-primary">{p.action}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

