
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/authStore";
import { 
  User as UserIcon, 
  UserCircle,
  MapPin
} from "lucide-react";

export default function Settings() {
  const { user } = useAuthStore();
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground">Manage your account and application preferences</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCircle className="h-6 w-6" />
            Profile Information
          </CardTitle>
          <CardDescription>
            View your personal information and section details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Full Name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-base">Full Name</Label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-3 h-6 w-6 text-muted-foreground" />
                <Input
                  id="name"
                  value={user?.name || ""}
                  className="pl-10 text-base disabled:opacity-100 disabled:text-foreground/80"
                  disabled
                />
              </div>
            </div>

            {/* Username */}
            <div className="space-y-2">
              <Label htmlFor="username" className="text-base">Username</Label>
              <Input
                id="username"
                value={user?.username || ""}
                className="text-base disabled:opacity-100 disabled:text-foreground/80"
                disabled
              />
            </div>

            {/* Section */}
            <div className="space-y-2">
              <Label htmlFor="section" className="text-base">Section</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-6 w-6 text-muted-foreground" />
                <Input
                  id="section"
                  value={user?.section || ""}
                  className="pl-10 text-base disabled:opacity-100 disabled:text-foreground/80"
                  disabled
                />
              </div>
            </div>
          </div>

          <Separator />
        </CardContent>
      </Card>
    </div>
  );
}