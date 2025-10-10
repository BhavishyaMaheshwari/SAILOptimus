import { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { 
  LayoutDashboard, 
  Settings,
  MapPin, 
  FileText, 
  PlayCircle, 
  LogOut,
  Train,
  Activity
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

interface AppLayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Simulation", href: "/simulation", icon: PlayCircle },
  { name: "Map", href: "/map", icon: MapPin },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation Sidebar */}
      <nav className="fixed left-0 top-0 h-full w-64 bg-nav border-r border-border shadow-medium z-40">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-nav-accent/20">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-nav-accent rounded-lg">
                <Train className="h-6 w-6 text-nav-accent-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-nav-foreground">
                  R<span className="text-nav-accent">AI</span>lOptimus
                </h1>
                <p className="text-xs text-nav-foreground/70">Section Control</p>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex-1 px-4 py-6">
            <div className="space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-nav-accent text-nav-accent-foreground shadow-sm"
                        : "text-nav-foreground hover:bg-nav-accent/10 hover:text-nav-accent"
                    }`}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* User Info & Logout */}
          <div className="p-4 border-t border-nav-accent/20">
            <Card className="bg-nav-accent/5 border-nav-accent/20 p-3">
              <div className="flex items-center space-x-3 mb-3">
                <div className="flex items-center justify-center w-8 h-8 bg-nav-accent/20 rounded-full">
                  <Activity className="h-4 w-4 text-nav-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-nav-foreground truncate">
                    {user?.name || "Section Controller"}
                  </p>
                  <p className="text-xs text-nav-foreground/70 truncate">
                    Section {user?.section || "A1"}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="w-full text-nav-foreground hover:bg-nav-accent/10 hover:text-nav-accent"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </Card>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="ml-64 min-h-screen">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}