import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { 
  BrainCircuit, 
  Send,
  Paperclip,
  Settings,
  Moon,
  Sun,
  Sparkles,
  Search,
  Zap
} from "lucide-react";

const Index = () => {
  const [message, setMessage] = useState("");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [activeMode, setActiveMode] = useState<"thinking" | "websearch" | "standard">("standard");
  const navigate = useNavigate();
  
  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    document.documentElement.classList.toggle("light");
  };

  const modes = [
    { id: "standard", label: "Standard", icon: Zap },
    { id: "thinking", label: "Thinking", icon: Sparkles },
    { id: "websearch", label: "Web Search", icon: Search },
  ] as const;
  
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <BrainCircuit className="w-6 h-6 text-background" />
            </div>
            <div>
              <h1 className="text-lg font-bold">JARVIS AI</h1>
              <p className="text-xs text-muted-foreground">Personal Assistant</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-2">
              <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
              Online
            </Badge>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={toggleTheme}
              className="rounded-lg"
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => navigate("/settings")}
              className="rounded-lg"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <div className="container mx-auto max-w-4xl px-4">
        <div className="flex flex-col h-[calc(100vh-8rem)] py-6">
          {/* Active Plugins Bar */}
          <div className="mb-4 flex items-center gap-2 p-3 rounded-lg bg-card border border-border">
            <span className="text-sm text-muted-foreground">Active Plugins:</span>
            <div className="flex gap-2">
              <Badge variant="secondary" className="gap-1">
                <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
                Code Analyzer
              </Badge>
              <Badge variant="secondary" className="gap-1">
                <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
                Web Search
              </Badge>
              <Badge variant="secondary" className="gap-1">
                <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                System Control
              </Badge>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 space-y-4 overflow-y-auto mb-4">
            {/* AI Message */}
            <div className="flex gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
                <BrainCircuit className="w-4 h-4 text-background" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="bg-card rounded-2xl rounded-tl-sm p-4 border border-border">
                  <p className="text-sm leading-relaxed">
                    Hello! I'm JARVIS, your personal AI assistant running locally on your system. 
                    I have full offline capability and can help you with various tasks. 
                    How can I assist you today?
                  </p>
                </div>
                <p className="text-xs text-muted-foreground px-2">2:34 PM</p>
              </div>
            </div>

            {/* User Message */}
            <div className="flex gap-3 justify-end animate-fade-in">
              <div className="flex-1 text-right space-y-2">
                <div className="bg-primary/10 rounded-2xl rounded-tr-sm p-4 border border-primary/20 inline-block max-w-[80%]">
                  <p className="text-sm leading-relaxed">Show me the system status</p>
                </div>
                <p className="text-xs text-muted-foreground px-2">2:35 PM</p>
              </div>
            </div>

            {/* AI Response */}
            <div className="flex gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
                <BrainCircuit className="w-4 h-4 text-background" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="bg-card rounded-2xl rounded-tl-sm p-4 border border-border space-y-3">
                  <p className="text-sm leading-relaxed">
                    You can check your system status in the Settings panel. Click the settings icon in the top right corner.
                  </p>
                  <div className="bg-muted/50 rounded-lg p-3 font-mono text-xs space-y-1">
                    <p className="text-accent">• Model: DeepSeek R1 (Active)</p>
                    <p className="text-primary">• Status: Running optimally</p>
                    <p className="text-muted-foreground">• Mode: Offline</p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground px-2">2:35 PM</p>
              </div>
            </div>
          </div>

          {/* Mode Selection */}
          <div className="mb-3 flex justify-center gap-2">
            {modes.map((mode) => {
              const Icon = mode.icon;
              return (
                <Button
                  key={mode.id}
                  variant={activeMode === mode.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveMode(mode.id as typeof activeMode)}
                  className="gap-2"
                >
                  <Icon className="w-3.5 h-3.5" />
                  {mode.label}
                </Button>
              );
            })}
          </div>

          {/* Input Area */}
          <div className="bg-card border border-border rounded-2xl p-3">
            <div className="flex gap-2 items-end">
              <Button
                size="icon"
                variant="ghost"
                className="flex-shrink-0 h-10 w-10 rounded-xl hover:bg-accent/10"
              >
                <Paperclip className="w-4 h-4" />
              </Button>
              
              <div className="flex-1">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask JARVIS anything..."
                  className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-sm"
                />
              </div>
              
              <Button 
                size="icon"
                className="flex-shrink-0 h-10 w-10 rounded-xl bg-primary hover:bg-primary/90"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            
            <div className="mt-2 flex items-center justify-between px-2">
              <p className="text-xs text-muted-foreground">
                {activeMode === "thinking" && "🧠 Deep reasoning mode"}
                {activeMode === "websearch" && "🔍 Web search enabled"}
                {activeMode === "standard" && "⚡ Standard mode"}
              </p>
              <p className="text-xs text-muted-foreground">
                100% offline • All data stays local
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
