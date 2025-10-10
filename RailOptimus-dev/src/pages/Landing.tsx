import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Train, Zap, Shield, BarChart3 } from "lucide-react";
import heroImage from "@/assets/railway-hero.jpg";
import Logo from "@/assets/railOptimus_Logo.png";

export default function Landing() {
  const features = [
    {
      icon: Train,
      title: "Real-time Tracking",
      description: "Monitor train movements and schedules in real-time across your section."
    },
    {
      icon: Zap,
      title: "AI-Powered Insights",
      description: "Get intelligent suggestions for optimal traffic management and conflict resolution."
    },
    {
      icon: Shield,
      title: "Safety First",
      description: "Built-in safety constraints ensure all operations meet railway safety standards."
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "Comprehensive reporting and analytics for performance optimization."
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card shadow-soft">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-12 h-11 bg-[white] rounded-lg">
                <img
                  src={Logo}
                  alt="Railway control center"
                  className="w-full h-full object-cover"
                />
                {/* <Train className="h-6 w-6 text-primary-foreground" /> */}
              </div>
              <h1 className="text-2xl font-bold text-foreground">
                R<span className="text-primary">AI</span>lOptimus
              </h1>
            </div>
            <div className="flex space-x-4">
              <Button variant="outline" asChild>
                <Link to="/login">Login</Link>
              </Button>
              <Button variant="hero" asChild>
                <Link to="/signup">Sign Up</Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img
            src={heroImage}
            alt="Railway control center"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-nav/80 to-nav/60" />
        </div>

        <div className="relative container mx-auto px-6 py-24">
          <div className="max-w-3xl">
            <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
              R<span className="text-nav-accent">AI</span>lOptimus
            </h1>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              AI powered decision support system for section controllers
            </p>
            <p className="text-lg text-white/80 mb-10 max-w-2xl">
              Transform railway operations with intelligent traffic management,
              real-time monitoring, and AI-driven decision support designed
              specifically for section controllers.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" variant="hero" asChild>
                <Link to="/signup">Get Started</Link>
              </Button>
              <Button size="lg" variant="outline" className="bg-white/10 border-white/30 text-white hover:bg-white/20" asChild>
                <Link to="/login">Sign In</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gradient-to-b from-background to-muted/30">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Professional Railway Control
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Built for section controllers who demand precision, safety, and efficiency
              in railway traffic management.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 hover:shadow-medium transition-all duration-300 border-border bg-card">
                <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg mb-4">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-3">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary/5">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Ready to Transform Your Railway Operations?
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join section controllers who trust RailOptimus for intelligent
            traffic management and decision support.
          </p>
          <Button size="lg" variant="hero" asChild>
            <Link to="/signup">Start Your Free Account</Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card py-8">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
                <Train className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">
                R<span className="text-primary">AI</span>lOptimus
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 RailOptimus. Professional railway control solutions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}