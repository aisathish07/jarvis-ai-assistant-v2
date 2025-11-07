import React, { useState, useEffect, useRef } from 'react';
import { Send, Paperclip, Mic, Search, Brain, Settings, Plug, Palette, MessageSquare, ChevronRight, X, Check, Loader, Zap, Upload } from 'lucide-react';

// API Configuration
const API_BASE = 'http://localhost:8080';
const WS_URL = 'ws://localhost:8080/ws';

// Theme definitions
const themes = {
  psychopass: {
    name: 'Psycho-Pass',
    primary: '#00D9FF',
    secondary: '#00FFA3',
    accent: '#FF006E',
    background: '#0A0E1A',
    surface: '#151B2E',
    surfaceHover: '#1E2740',
    text: '#E0E7FF',
    textMuted: '#8B9DC3',
    border: '#2A3F5F',
    success: '#00FF88',
    warning: '#FFB800',
    error: '#FF3366',
  },
  neonCyber: {
    name: 'Neon Cyberpunk',
    primary: '#FF00FF',
    secondary: '#00FFFF',
    accent: '#FFFF00',
    background: '#0D0D0D',
    surface: '#1A1A1A',
    surfaceHover: '#262626',
    text: '#FFFFFF',
    textMuted: '#999999',
    border: '#333333',
    success: '#00FF00',
    warning: '#FFA500',
    error: '#FF0000',
  },
  animePastel: {
    name: 'Anime Pastel',
    primary: '#FF6B9D',
    secondary: '#8B7FFF',
    accent: '#FFC46B',
    background: '#1A1625',
    surface: '#2D2640',
    surfaceHover: '#3D3555',
    text: '#F5E6FF',
    textMuted: '#B8A8CC',
    border: '#4A4160',
    success: '#7FFF9D',
    warning: '#FFD67F',
    error: '#FF6B6B',
  },
};

const JarvisApp = () => {
  const [currentTheme, setCurrentTheme] = useState('psychopass');
  const [activeView, setActiveView] = useState('chat');
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [thinkingMode, setThinkingMode] = useState(false);
  const [plugins, setPlugins] = useState([]);
  const [selectedModel, setSelectedModel] = useState('phi3:3.8b');
  const [availableModels, setAvailableModels] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const wsRef = useRef(null);
  const currentMessageRef = useRef('');

  const theme = themes[currentTheme];

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    loadSettings();
    fetchPlugins();
    fetchModels();
    fetchSystemStatus();
    
    // Poll system status every 5 seconds
    const statusInterval = setInterval(fetchSystemStatus, 5000);
    
    return () => {
      clearInterval(statusInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Save settings when theme changes
  useEffect(() => {
    saveSettings();
  }, [currentTheme, selectedModel]);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnectionStatus('connected');
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'system',
          content: 'Connected to JARVIS. Ready to assist!',
          timestamp: new Date(),
        }]);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        // Attempt reconnection after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'status':
        if (data.status === 'thinking') {
          setIsThinking(true);
        }
        break;
        
      case 'chunk':
        // Update current streaming message
        currentMessageRef.current = data.full;
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.type === 'assistant' && lastMsg.streaming) {
            return [...prev.slice(0, -1), {
              ...lastMsg,
              content: data.full,
            }];
          } else {
            return [...prev, {
              id: Date.now(),
              type: 'assistant',
              content: data.full,
              timestamp: new Date(),
              streaming: true,
            }];
          }
        });
        break;
        
      case 'complete':
        setIsThinking(false);
        currentMessageRef.current = '';
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.streaming) {
            return [...prev.slice(0, -1), {
              ...lastMsg,
              streaming: false,
            }];
          }
          return prev;
        });
        break;
        
      case 'error':
        setIsThinking(false);
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'error',
          content: `Error: ${data.message}`,
          timestamp: new Date(),
        }]);
        break;
        
      case 'pong':
        // Keep-alive response
        break;
    }
  };

  const handleSendMessage = () => {
    if (!inputText.trim() || connectionStatus !== 'connected') return;

    const newMessage = {
      id: Date.now(),
      type: 'user',
      content: inputText,
      timestamp: new Date(),
      webSearch: webSearchEnabled,
      thinking: thinkingMode,
    };

    setMessages(prev => [...prev, newMessage]);
    setInputText('');

    // Send via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        message: inputText,
        webSearch: webSearchEnabled,
        thinkingMode: thinkingMode,
        model: selectedModel,
      }));
    }
  };

  const handleFileAttach = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    // Create FormData
    const formData = new FormData();
    files.forEach(file => {
      formData.append('file', file);
    });

    try {
      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (result.success) {
        const fileMessage = {
          id: Date.now(),
          type: 'user',
          content: `📎 Uploaded ${files.length} file(s): ${files.map(f => f.name).join(', ')}`,
          timestamp: new Date(),
          files: result.files,
        };
        setMessages(prev => [...prev, fileMessage]);
      }
    } catch (error) {
      console.error('File upload error:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'error',
        content: `Failed to upload files: ${error.message}`,
        timestamp: new Date(),
      }]);
    }
  };

  const fetchPlugins = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/plugins`);
      const data = await response.json();
      
      if (data.plugins) {
        setPlugins(data.plugins.map((p, i) => ({
          id: p.id,
          name: p.name,
          active: p.active,
          icon: ['🌤️', '🔍', '📁', '💻', '⚙️', '🎵', '📊'][i % 7],
        })));
      }
    } catch (error) {
      console.error('Failed to fetch plugins:', error);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/models`);
      const data = await response.json();
      
      if (data.models) {
        setAvailableModels(data.models);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
      // Fallback to default models
      setAvailableModels([
        { name: 'phi3:3.8b', size: 0 },
        { name: 'gemma:2b', size: 0 },
        { name: 'deepseek-coder:6.7b', size: 0 },
      ]);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const togglePlugin = async (id) => {
    const plugin = plugins.find(p => p.id === id);
    if (!plugin) return;

    try {
      await fetch(`${API_BASE}/api/plugins/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plugin_id: id,
          enabled: !plugin.active,
        }),
      });

      setPlugins(plugins.map(p => p.id === id ? { ...p, active: !p.active } : p));
    } catch (error) {
      console.error('Failed to toggle plugin:', error);
    }
  };

  const saveSettings = async () => {
    try {
      await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          theme: currentTheme,
          model: selectedModel,
        }),
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/settings`);
      const data = await response.json();
      
      if (data.theme) setCurrentTheme(data.theme);
      if (data.model) setSelectedModel(data.model);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  return (
    <div style={{ 
      backgroundColor: theme.background, 
      color: theme.text, 
      minHeight: '100vh',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated background grid */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `linear-gradient(${theme.border} 1px, transparent 1px), linear-gradient(90deg, ${theme.border} 1px, transparent 1px)`,
        backgroundSize: '50px 50px',
        opacity: 0.1,
        animation: 'gridMove 20s linear infinite',
      }} />

      {/* Top Bar */}
      <div style={{
        height: '60px',
        backgroundColor: theme.surface,
        borderBottom: `1px solid ${theme.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'relative',
        zIndex: 10,
        boxShadow: `0 4px 20px ${theme.primary}20`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            background: `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '2px',
          }}>
            JARVIS
          </div>
          <div style={{
            fontSize: '12px',
            color: connectionStatus === 'connected' ? theme.success : theme.error,
            padding: '4px 8px',
            backgroundColor: connectionStatus === 'connected' ? `${theme.success}20` : `${theme.error}20`,
            borderRadius: '4px',
            border: `1px solid ${connectionStatus === 'connected' ? theme.success : theme.error}40`,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: connectionStatus === 'connected' ? theme.success : theme.error,
              animation: connectionStatus === 'connected' ? 'pulse 2s infinite' : 'none',
            }} />
            {connectionStatus.toUpperCase()}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            style={{
              backgroundColor: theme.surface,
              color: theme.text,
              border: `1px solid ${theme.border}`,
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {availableModels.map(model => (
              <option key={model.name} value={model.name}>
                {model.name}
              </option>
            ))}
          </select>
          
          <button
            onClick={() => setActiveView('settings')}
            style={{
              background: 'transparent',
              border: `1px solid ${theme.border}`,
              color: theme.text,
              padding: '8px',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = theme.primary;
              e.currentTarget.style.boxShadow = `0 0 12px ${theme.primary}40`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = theme.border;
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <Settings size={20} />
          </button>
        </div>
      </div>

      {/* Main Layout */}
      <div style={{ display: 'flex', height: 'calc(100vh - 60px)', position: 'relative', zIndex: 1 }}>
        {/* Sidebar */}
        <div style={{
          width: '80px',
          backgroundColor: theme.surface,
          borderRight: `1px solid ${theme.border}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          padding: '16px 8px',
        }}>
          {[
            { id: 'chat', icon: MessageSquare, label: 'Chat' },
            { id: 'plugins', icon: Plug, label: 'Plugins' },
            { id: 'themes', icon: Palette, label: 'Themes' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              style={{
                background: activeView === item.id ? `${theme.primary}20` : 'transparent',
                border: activeView === item.id ? `1px solid ${theme.primary}` : `1px solid transparent`,
                color: activeView === item.id ? theme.primary : theme.textMuted,
                padding: '12px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                fontSize: '10px',
                transition: 'all 0.3s',
              }}
              onMouseEnter={(e) => {
                if (activeView !== item.id) {
                  e.currentTarget.style.backgroundColor = `${theme.surfaceHover}`;
                }
              }}
              onMouseLeave={(e) => {
                if (activeView !== item.id) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              <item.icon size={24} />
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Chat View */}
          {activeView === 'chat' && (
            <>
              {/* Messages Area */}
              <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}>
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    style={{
                      display: 'flex',
                      justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
                      animation: 'slideIn 0.3s ease-out',
                    }}
                  >
                    <div
                      style={{
                        maxWidth: '70%',
                        padding: '16px',
                        borderRadius: '12px',
                        backgroundColor: msg.type === 'user' ? `${theme.primary}20` : 
                                       msg.type === 'error' ? `${theme.error}20` :
                                       msg.type === 'system' ? `${theme.secondary}20` : theme.surface,
                        border: `1px solid ${msg.type === 'user' ? theme.primary : 
                                           msg.type === 'error' ? theme.error :
                                           msg.type === 'system' ? theme.secondary : theme.border}`,
                        boxShadow: `0 4px 12px ${msg.type === 'user' ? theme.primary : theme.surface}40`,
                      }}
                    >
                      <div style={{ fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                        {msg.content}
                      </div>
                      <div style={{
                        fontSize: '11px',
                        color: theme.textMuted,
                        marginTop: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}>
                        {msg.timestamp.toLocaleTimeString()}
                        {msg.webSearch && <span style={{ color: theme.secondary }}>🔍 Web</span>}
                        {msg.thinking && <span style={{ color: theme.accent }}>🧠 Deep</span>}
                        {msg.streaming && <span style={{ color: theme.primary }}>⚡ Streaming</span>}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isThinking && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.textMuted }}>
                    <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    <span>JARVIS is analyzing...</span>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div style={{
                padding: '24px',
                backgroundColor: theme.surface,
                borderTop: `1px solid ${theme.border}`,
              }}>
                {/* Mode Toggles */}
                <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
                  <button
                    onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: `1px solid ${webSearchEnabled ? theme.secondary : theme.border}`,
                      backgroundColor: webSearchEnabled ? `${theme.secondary}20` : 'transparent',
                      color: webSearchEnabled ? theme.secondary : theme.textMuted,
                      cursor: 'pointer',
                      fontSize: '13px',
                      transition: 'all 0.3s',
                    }}
                  >
                    <Search size={16} />
                    Web Search
                    {webSearchEnabled && <Check size={14} />}
                  </button>

                  <button
                    onClick={() => setThinkingMode(!thinkingMode)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: `1px solid ${thinkingMode ? theme.accent : theme.border}`,
                      backgroundColor: thinkingMode ? `${theme.accent}20` : 'transparent',
                      color: thinkingMode ? theme.accent : theme.textMuted,
                      cursor: 'pointer',
                      fontSize: '13px',
                      transition: 'all 0.3s',
                    }}
                  >
                    <Brain size={16} />
                    Deep Thinking
                    {thinkingMode && <Check size={14} />}
                  </button>
                </div>

                {/* Input Box */}
                <div style={{
                  display: 'flex',
                  gap: '12px',
                  alignItems: 'flex-end',
                }}>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    multiple
                    style={{ display: 'none' }}
                  />
                  
                  <button
                    onClick={handleFileAttach}
                    disabled={connectionStatus !== 'connected'}
                    style={{
                      background: 'transparent',
                      border: `1px solid ${theme.border}`,
                      color: connectionStatus === 'connected' ? theme.textMuted : theme.border,
                      padding: '12px',
                      borderRadius: '8px',
                      cursor: connectionStatus === 'connected' ? 'pointer' : 'not-allowed',
                      display: 'flex',
                      alignItems: 'center',
                      transition: 'all 0.3s',
                    }}
                    onMouseEnter={(e) => {
                      if (connectionStatus === 'connected') {
                        e.currentTarget.style.borderColor = theme.primary;
                        e.currentTarget.style.color = theme.primary;
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = theme.border;
                      e.currentTarget.style.color = theme.textMuted;
                    }}
                  >
                    <Paperclip size={20} />
                  </button>

                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder={connectionStatus === 'connected' ? 'Type your message...' : 'Connecting...'}
                    disabled={connectionStatus !== 'connected'}
                    style={{
                      flex: 1,
                      backgroundColor: theme.background,
                      border: `1px solid ${theme.border}`,
                      borderRadius: '8px',
                      padding: '12px 16px',
                      color: theme.text,
                      fontSize: '14px',
                      outline: 'none',
                      transition: 'all 0.3s',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = theme.primary;
                      e.target.style.boxShadow = `0 0 0 3px ${theme.primary}20`;
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = theme.border;
                      e.target.style.boxShadow = 'none';
                    }}
                  />

                  <button
                    onClick={handleSendMessage}
                    disabled={!inputText.trim() || connectionStatus !== 'connected'}
                    style={{
                      background: inputText.trim() && connectionStatus === 'connected' ? 
                        `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})` : theme.surface,
                      border: 'none',
                      color: theme.background,
                      padding: '12px 24px',
                      borderRadius: '8px',
                      cursor: inputText.trim() && connectionStatus === 'connected' ? 'pointer' : 'not-allowed',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      transition: 'all 0.3s',
                      opacity: inputText.trim() && connectionStatus === 'connected' ? 1 : 0.5,
                    }}
                  >
                    <Send size={18} />
                    Send
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Plugins View */}
          {activeView === 'plugins' && (
            <div style={{ padding: '24px', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '24px', marginBottom: '24px', color: theme.primary }}>
                Active Plugins
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '16px' }}>
                {plugins.map((plugin) => (
                  <div
                    key={plugin.id}
                    style={{
                      backgroundColor: theme.surface,
                      border: `1px solid ${plugin.active ? theme.primary : theme.border}`,
                      borderRadius: '12px',
                      padding: '20px',
                      transition: 'all 0.3s',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-4px)';
                      e.currentTarget.style.boxShadow = `0 8px 20px ${theme.primary}30`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <span style={{ fontSize: '32px' }}>{plugin.icon}</span>
                      <button
                        onClick={() => togglePlugin(plugin.id)}
                        style={{
                          width: '48px',
                          height: '24px',
                          backgroundColor: plugin.active ? theme.success : theme.border,
                          border: 'none',
                          borderRadius: '12px',
                          cursor: 'pointer',
                          position: 'relative',
                          transition: 'all 0.3s',
                        }}
                      >
                        <div style={{
                          width: '18px',
                          height: '18px',
                          backgroundColor: 'white',
                          borderRadius: '50%',
                          position: 'absolute',
                          top: '3px',
                          left: plugin.active ? '27px' : '3px',
                          transition: 'all 0.3s',
                        }} />
                      </button>
                    </div>
                    <h3 style={{ fontSize: '16px', marginBottom: '4px' }}>{plugin.name}</h3>
                    <p style={{ fontSize: '12px', color: theme.textMuted }}>
                      {plugin.active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Themes View */}
          {activeView === 'themes' && (
            <div style={{ padding: '24px', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '24px', marginBottom: '24px', color: theme.primary }}>
                Choose Your Theme
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
                {Object.entries(themes).map(([key, t]) => (
                  <div
                    key={key}
                    onClick={() => setCurrentTheme(key)}
                    style={{
                      backgroundColor: t.surface,
                      border: `2px solid ${currentTheme === key ? theme.primary : t.border}`,
                      borderRadius: '12px',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.3s',
                      position: 'relative',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.05)';
                      e.currentTarget.style.boxShadow = `0 8px 20px ${t.primary}30`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    {currentTheme === key && (
                      <div style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        backgroundColor: theme.primary,
                        borderRadius: '50%',
                        padding: '4px',
                      }}>
                        <Check size={16} color={theme.background} />
                      </div>
                    )}
                    <h3 style={{ color: t.text, marginBottom: '12px' }}>{t.name}</h3>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {[t.primary, t.secondary, t.accent].map((color, i) => (
                        <div
                          key={i}
                          style={{
                            width: '40px',
                            height: '40px',
                            backgroundColor: color,
                            borderRadius: '8px',
                            boxShadow: `0 0 12px ${color}60`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Settings View */}
          {activeView === 'settings' && (
            <div style={{ padding: '24px', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '24px', marginBottom: '24px', color: theme.primary }}>
                Settings
              </h2>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '600px' }}>
                {/* System Status */}
                <div style={{
                  backgroundColor: theme.surface,
                  border: `1px solid ${theme.border}`,
                  borderRadius: '12px',
                  padding: '20px',
                }}>
                  <h3 style={{ fontSize: '18px', marginBottom: '16px', color: theme.secondary }}>
                    System Status
                  </h3>
                  {systemStatus ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: theme.textMuted }}>CPU Usage</span>
                        <span style={{ color: theme.success }}>{systemStatus.system?.cpu_usage || 'N/A'}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: theme.textMuted }}>Memory</span>
                        <span style={{ color: theme.success }}>
                          {systemStatus.system?.memory_used || 'N/A'} / {systemStatus.system?.memory_total || 'N/A'}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: theme.textMuted }}>Active Model</span>
                        <span style={{ color: theme.primary }}>{selectedModel}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: theme.textMuted }}>Active Plugins</span>
                        <span style={{ color: theme.secondary }}>
                          {plugins.filter(p => p.active).length}/{plugins.length}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: theme.textMuted }}>Total Queries</span>
                        <span style={{ color: theme.primary }}>
                          {systemStatus.jarvis?.total_queries || 0}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.textMuted }}>
                      <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} />
                      <span>Loading system status...</span>
                    </div>
                  )}
                </div>

                {/* API Configuration */}
                <div style={{
                  backgroundColor: theme.surface,
                  border: `1px solid ${theme.border}`,
                  borderRadius: '12px',
                  padding: '20px',
                }}>
                  <h3 style={{ fontSize: '18px', marginBottom: '16px', color: theme.secondary }}>
                    API Configuration
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <input
                      type="password"
                      placeholder="OpenAI API Key (Optional)"
                      style={{
                        backgroundColor: theme.background,
                        border: `1px solid ${theme.border}`,
                        borderRadius: '6px',
                        padding: '10px 12px',
                        color: theme.text,
                        fontSize: '14px',
                        outline: 'none',
                      }}
                    />
                    <input
                      type="password"
                      placeholder="Gemini API Key (Optional)"
                      style={{
                        backgroundColor: theme.background,
                        border: `1px solid ${theme.border}`,
                        borderRadius: '6px',
                        padding: '10px 12px',
                        color: theme.text,
                        fontSize: '14px',
                        outline: 'none',
                      }}
                    />
                  </div>
                </div>

                {/* Connection Info */}
                <div style={{
                  backgroundColor: theme.surface,
                  border: `1px solid ${theme.border}`,
                  borderRadius: '12px',
                  padding: '20px',
                }}>
                  <h3 style={{ fontSize: '18px', marginBottom: '16px', color: theme.secondary }}>
                    Connection Info
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: theme.textMuted }}>API Server</span>
                      <span style={{ color: theme.text, fontSize: '12px', fontFamily: 'monospace' }}>
                        {API_BASE}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: theme.textMuted }}>WebSocket</span>
                      <span style={{ color: theme.text, fontSize: '12px', fontFamily: 'monospace' }}>
                        {WS_URL}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: theme.textMuted }}>Status</span>
                      <span style={{ 
                        color: connectionStatus === 'connected' ? theme.success : theme.error,
                        fontWeight: 'bold'
                      }}>
                        {connectionStatus.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes gridMove {
          0% { transform: translateY(0); }
          100% { transform: translateY(50px); }
        }
        
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        input::placeholder {
          color: ${theme.textMuted};
          opacity: 0.6;
        }

        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: ${theme.background};
        }

        ::-webkit-scrollbar-thumb {
          background: ${theme.border};
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: ${theme.primary};
        }
      `}</style>
    </div>
  );
};

export default JarvisApp;
