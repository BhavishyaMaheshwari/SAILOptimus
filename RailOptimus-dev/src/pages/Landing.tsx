import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Anchor, Zap, Shield, BarChart3 } from "lucide-react";
import heroImage from "@/assets/railway-hero.jpg";
import Logo from "@/assets/railOptimus_Logo.png";
import navbar from "@/assets/navbar.png";
import "@/styles/fonts.css";

export default function Landing() {
  const features = [
    {
      icon: Anchor,
      title: "Real-time Tracking",
      description: "Monitor vessel, berthing, and freight delays in real time to enhance scheduling accuracy and operational control."
    },
    {
      icon: Zap,
      title: "AI-Powered Insights",
      description: "Gain data-driven analytics for optimal vessel scheduling, port selection, and cost-efficient logistics planning."
    },
    {
      icon: Shield,
      title: "Operational Reliability",
      description: "Integrated system constraints ensure all logistics decisions maintain compliance, safety, and process integrity."
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "Access detailed reports and analytics to evaluate efficiency, identify bottlenecks, and optimize overall logistics performance."
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header
        className="border-b border-border shadow-soft"
        style={{
          backgroundImage: `url(${navbar})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-15 h-11 rounded-lg">
                <img src={Logo} alt="Port control center (SAIL)" className="w-full h-full object-cover" />
                {/* <Train className="h-6 w-6 text-primary-foreground" /> */}
              </div>
              {/* <h1 className="text-2xl font-bold text-foreground">
                R<span className="text-primary">AI</span>lOptimus
              </h1> */}
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
              S<span className="text-nav-accent">AI</span>LOptimus
            </h1>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              AI-Powered Delay Prediction System for Steel Logistics Operations
            </p>
            <p className="text-xl text-white/95 mb-14 max-w-2xl eb-garamond">
              Optimize vessel, port, and freight operations with a machine learning-based logistics dashboard designed for SAIL. The system integrates Random Forest models to predict vessel, berthing, and freight delays in real time using parameters such as port congestion, rake availability, and plant utilization, enabling data-driven, cost-optimal scheduling and improved operational efficiency.
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
              Advanced Logistics Control
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Designed for operations managers who prioritize precision, reliability, and efficiency in end-to-end steel logistics management.
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
            Predict and Optimize Steel Logistics with SAIL
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Predict vessel, berthing, and train delays in real time and make data-driven decisions to streamline steel logistics and maximize operational efficiency.
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
                <Anchor className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">
                S<span className="text-primary">AI</span>L
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 SAIL. Intelligent logistics optimization solutions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}