import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  FileText, 
  Download, 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  CheckCircle, 
  XCircle,
  Clock,
  AlertTriangle,
  BarChart3
} from "lucide-react";

interface DailySummary {
  date: string;
  handledDelays: number;
  resolvedConflicts: number;
  emergencies: number;
  approvedSuggestions: number;
  rejectedSuggestions: number;
  totalSuggestions: number;
}

interface SuggestionDetail {
  id: string;
  time: string;
  type: "rescheduling" | "route_change" | "priority_adjustment";
  description: string;
  status: "approved" | "rejected" | "pending";
  impact: "low" | "medium" | "high";
}

const mockSummaries: DailySummary[] = [
  {
    date: "2024-01-15",
    handledDelays: 12,
    resolvedConflicts: 5,
    emergencies: 2,
    approvedSuggestions: 8,
    rejectedSuggestions: 3,
    totalSuggestions: 11
  },
  {
    date: "2024-01-14",
    handledDelays: 8,
    resolvedConflicts: 3,
    emergencies: 1,
    approvedSuggestions: 6,
    rejectedSuggestions: 2,
    totalSuggestions: 8
  },
  {
    date: "2024-01-13",
    handledDelays: 15,
    resolvedConflicts: 7,
    emergencies: 3,
    approvedSuggestions: 10,
    rejectedSuggestions: 4,
    totalSuggestions: 14
  },
  {
    date: "2024-01-12",
    handledDelays: 6,
    resolvedConflicts: 2,
    emergencies: 0,
    approvedSuggestions: 4,
    rejectedSuggestions: 1,
    totalSuggestions: 5
  },
  {
    date: "2024-01-11",
    handledDelays: 10,
    resolvedConflicts: 4,
    emergencies: 1,
    approvedSuggestions: 7,
    rejectedSuggestions: 2,
    totalSuggestions: 9
  }
];

const mockSuggestions: SuggestionDetail[] = [
  {
    id: "1",
    time: "09:15",
    type: "rescheduling",
    description: "Delay TR001 by 10 minutes to avoid conflict at Junction A2",
    status: "approved",
    impact: "medium"
  },
  {
    id: "2",
    time: "10:30",
    type: "route_change",
    description: "Redirect TR003 through Loop Line B1 due to block closure",
    status: "approved",
    impact: "high"
  },
  {
    id: "3",
    time: "11:45",
    type: "priority_adjustment",
    description: "Prioritize Express TR004 over Local TR002 at Platform 2",
    status: "rejected",
    impact: "low"
  },
  {
    id: "4",
    time: "13:20",
    type: "rescheduling",
    description: "Advance TR005 by 5 minutes to optimize throughput",
    status: "approved",
    impact: "medium"
  },
  {
    id: "5",
    time: "14:10",
    type: "route_change",
    description: "Use alternate route for TR001 due to maintenance work",
    status: "pending",
    impact: "high"
  }
];

export default function Reports() {
  const [selectedDate, setSelectedDate] = useState("2024-01-15");
  const [reportType, setReportType] = useState("daily");
  const [exportFormat, setExportFormat] = useState("csv");

  const selectedSummary = mockSummaries.find(s => s.date === selectedDate) || mockSummaries[0];
  const approvalRate = (selectedSummary.approvedSuggestions / selectedSummary.totalSuggestions * 100).toFixed(1);

  const exportReport = () => {
    // Mock export functionality
    const filename = `railway_report_${selectedDate}.${exportFormat}`;
    console.log(`Exporting ${filename}...`);
    // In a real app, this would generate and download the file
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return <CheckCircle className="h-4 w-4 text-success" />;
      case "rejected":
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return <Clock className="h-4 w-4 text-warning" />;
    }
  };

  const getImpactBadge = (impact: string) => {
    const variants = {
      low: "secondary",
      medium: "warning",
      high: "destructive"
    } as const;
    
    return <Badge variant={variants[impact as keyof typeof variants]}>{impact}</Badge>;
  };

  const getTypeLabel = (type: string) => {
    const labels = {
      rescheduling: "Rescheduling",
      route_change: "Route Change",
      priority_adjustment: "Priority Adj."
    };
    return labels[type as keyof typeof labels] || type;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Reports & Analytics</h1>
          <p className="text-muted-foreground">Daily summaries and operational insights</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={exportFormat} onValueChange={setExportFormat}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="pdf">PDF</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={exportReport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Report Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-4">
          <div className="space-y-2">
            <Label htmlFor="report-type">Report Type</Label>
            <Select value={reportType} onValueChange={setReportType}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily Summary</SelectItem>
                <SelectItem value="weekly">Weekly Summary</SelectItem>
                <SelectItem value="monthly">Monthly Summary</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="date">Date</Label>
            <Input
              id="date"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-40"
            />
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-warning" />
              <span className="text-sm font-medium">Handled Delays</span>
            </div>
            <div className="text-2xl font-bold mt-2">{selectedSummary.handledDelays}</div>
            <div className="text-xs text-muted-foreground">incidents resolved</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <span className="text-sm font-medium">Conflicts Resolved</span>
            </div>
            <div className="text-2xl font-bold mt-2">{selectedSummary.resolvedConflicts}</div>
            <div className="text-xs text-muted-foreground">scheduling conflicts</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <span className="text-sm font-medium">Emergencies</span>
            </div>
            <div className="text-2xl font-bold mt-2">{selectedSummary.emergencies}</div>
            <div className="text-xs text-muted-foreground">emergency situations</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-success" />
              <span className="text-sm font-medium">Approval Rate</span>
            </div>
            <div className="text-2xl font-bold mt-2">{approvalRate}%</div>
            <div className="text-xs text-muted-foreground">AI suggestions approved</div>
          </CardContent>
        </Card>
      </div>

      {/* Suggestions Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              AI Suggestions Summary
            </CardTitle>
            <CardDescription>Approved vs Rejected suggestions for {selectedDate}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-success" />
                  <span className="text-sm">Approved</span>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{selectedSummary.approvedSuggestions}</div>
                  <div className="text-xs text-muted-foreground">
                    {((selectedSummary.approvedSuggestions / selectedSummary.totalSuggestions) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-destructive" />
                  <span className="text-sm">Rejected</span>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{selectedSummary.rejectedSuggestions}</div>
                  <div className="text-xs text-muted-foreground">
                    {((selectedSummary.rejectedSuggestions / selectedSummary.totalSuggestions) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between font-medium">
                <span>Total Suggestions</span>
                <span>{selectedSummary.totalSuggestions}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Weekly Trend</CardTitle>
            <CardDescription>Performance over the past 5 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockSummaries.map((summary, index) => (
                <div key={summary.date} className="flex items-center justify-between">
                  <div className="text-sm">{summary.date}</div>
                  <div className="flex items-center gap-4">
                    <div className="text-xs text-muted-foreground">
                      {summary.handledDelays} delays
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {summary.resolvedConflicts} conflicts
                    </div>
                    <div className="flex items-center gap-1">
                      {index === 0 ? (
                        <TrendingUp className="h-3 w-3 text-success" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Suggestions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            AI Suggestions Detail
          </CardTitle>
          <CardDescription>All suggestions for {selectedDate}</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Impact</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockSuggestions.map((suggestion) => (
                <TableRow key={suggestion.id}>
                  <TableCell className="font-mono text-sm">{suggestion.time}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{getTypeLabel(suggestion.type)}</Badge>
                  </TableCell>
                  <TableCell className="max-w-md">{suggestion.description}</TableCell>
                  <TableCell>{getImpactBadge(suggestion.impact)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(suggestion.status)}
                      <span className="capitalize text-sm">{suggestion.status}</span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}