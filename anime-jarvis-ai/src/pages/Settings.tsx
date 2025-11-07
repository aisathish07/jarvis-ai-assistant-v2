import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Activity, 
  Cpu, 
  Database,
  BarChart3,
  Shield,
  Plug,
  ArrowLeft
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const Settings = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/")}
              className="rounded-lg"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <h1 className="text-lg font-bold">Settings</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto max-w-6xl px-4 py-6 space-y-6">
        {/* System Status */}
        <Card className="bg-card border-border p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            System Status
          </h2>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">GPU Usage</span>
                <span className="text-primary font-mono">67%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-primary to-accent w-[67%]" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">VRAM</span>
                <span className="text-accent font-mono">8.2 / 12 GB</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-accent to-primary w-[68%]" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">RAM</span>
                <span className="text-primary font-mono">16.5 / 32 GB</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-primary to-accent w-[52%]" />
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Active Model</span>
                <Badge className="bg-primary/20 text-primary border-primary/50">
                  DeepSeek R1
                </Badge>
              </div>
            </div>
          </div>
        </Card>

        {/* Performance Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-card border-border p-4">
            <Cpu className="w-8 h-8 text-primary mb-2" />
            <p className="text-2xl font-bold font-mono">94%</p>
            <p className="text-xs text-muted-foreground">Performance</p>
          </Card>
          
          <Card className="bg-card border-border p-4">
            <Activity className="w-8 h-8 text-accent mb-2" />
            <p className="text-2xl font-bold font-mono">1.2s</p>
            <p className="text-xs text-muted-foreground">Response Time</p>
          </Card>

          <Card className="bg-card border-border p-4">
            <Shield className="w-8 h-8 text-primary mb-2" />
            <p className="text-2xl font-bold font-mono">100%</p>
            <p className="text-xs text-muted-foreground">Offline Mode</p>
          </Card>
        </div>

        {/* Plugin Management */}
        <Card className="bg-card border-border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Plug className="w-5 h-5 text-accent" />
            Plugin Management
          </h3>
          <div className="space-y-2">
            {[
              { name: "Code Analyzer", icon: Database, status: "active" },
              { name: "Web Search", icon: BarChart3, status: "active" },
              { name: "System Control", icon: Shield, status: "standby" },
            ].map((plugin) => (
              <div key={plugin.name} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
                <div className="flex items-center gap-3">
                  <plugin.icon className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">{plugin.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={plugin.status === 'active' ? 'default' : 'secondary'}>
                    {plugin.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    Configure
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
