import { useEffect, useRef, useState } from "react";
import ReactDOM from 'react-dom/client';
import LoginPage from './Login.jsx'; 
import "./App.css";

const RootApp = () => {
  const [loggedIn, setLoggedIn] = useState(false);

  const handleLoginSuccess = () => {
    setLoggedIn(true);
  };

  const handleLogout = () => {
    setLoggedIn(false);
  };

  return loggedIn ? <ChatApp onLogout={handleLogout} /> : <LoginPage onLoginSuccess={handleLoginSuccess} />;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<RootApp />);

function ChatApp({ onLogout }) {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem("chatHistory");
    return saved ? JSON.parse(saved) : [
      { 
        sender: "bot", 
        text: "Hello! I'm MemeLord, the funniest bot around. How can I make you laugh today?", 
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }
    ];
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const savedMode = localStorage.getItem("darkMode");
    return savedMode ? JSON.parse(savedMode) : false;
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const messageEndRef = useRef(null);
  const messageContainerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("darkMode", JSON.stringify(darkMode));
  }, [darkMode]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
    localStorage.setItem("chatHistory", JSON.stringify(messages));
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage = { sender: "user", text: input, time: timestamp };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        { sender: "bot", isTyping: true, time: timestamp }
      ]);

      setTimeout(() => {
        setMessages((prev) => {
          const newMessages = [...prev];
          newMessages.pop();

          newMessages.push({
            sender: "bot",
            text: data.reply,
            meme_url: data.meme_url || null,
            time: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          });

          return newMessages;
        });
      }, 1000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error.";
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: `💀 Oops: ${errorMessage}`,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setInput("");
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  const clearChat = () => {
    if (window.confirm("Are you sure you want to clear chat history?")) {
      setMessages([{
        sender: "bot",
        text: "Chat history cleared! How can I help you today?",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }]);
    }
  };

  const filteredMessages = searchQuery 
    ? messages.filter(msg => 
        msg.text && msg.text.toLowerCase().includes(searchQuery.toLowerCase()))
    : messages;

  const renderTypingIndicator = () => (
    <div className="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  );

  return (
    <div className={`app-wrapper ${darkMode ? "dark" : "light"}`}>
      <button className="logout-button" onClick={onLogout}>
        Logout
      </button>

      <button 
        className={`menu-toggle ${sidebarOpen ? 'active' : ''}`}
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={{ marginLeft: '70px' }}
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>MemeLord</h2>
          <div className="sidebar-close" onClick={() => setSidebarOpen(false)}>×</div>
          <span className="toggle-label"></span>
          <label className="switch">
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
            />
            <span className="slider round"></span>
          </label>
          <span className="toggle-icon">{darkMode ? "☀️" : "🌙"}</span>
        </div>
        
        <input 
          type="text" 
          className="search" 
          placeholder="Search messages..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <p className="bot-intro">
         Welcome to <strong>MemeLord</strong> your personal AI comic relief. I'm here to spice up your day with dark humor, sarcastic one-liners, and the dankest memes on the internet. Whether you're feeling down, bored, or just need a laugh that makes you question your morals, I’ve got your back. Type anything, and prepare for some brainrot brilliance. Let's ruin your sense of humor together. 
        </p>
        
        <div className="sidebar-actions">
          <button className="action-button" onClick={clearChat}>
            Clear Chat
          </button>
        </div>
        
        <div className="app-info">
          <p>Version 2.0</p>
          <p>© 2025 MemeLord</p>
        </div>
      </aside>

      <div className="conversation-container">
        <img src="/logo.png" alt="MemeLord Logo" className="app-logo" />

        <div className="message-container" ref={messageContainerRef}>
          {filteredMessages.map((msg, idx) => (
            <div
              key={idx}
              className={`message ${msg.sender === "user" ? "user-message" : "bot-message"} ${idx === messages.length - 1 ? "latest" : ""}`}
            >
              <div className="message-header">
                <span className="sender-name">
                  {msg.sender === "user" ? "You" : "MemeLord"}
                </span>
                <div className="timestamp">{msg.time}</div>
              </div>
              
              {msg.isTyping ? renderTypingIndicator() : (
                <>
                  <p className="message-text">{msg.text}</p>
                  {msg.meme_url && (
                    <div className="meme-container">
                      <img src={msg.meme_url} alt="Meme" loading="lazy" />
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
          <div ref={messageEndRef} />
        </div>

        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={input}
            disabled={loading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type something..."
          />
          <button 
            className={`send-button ${loading ? 'loading' : ''}`} 
            onClick={sendMessage} 
            disabled={loading}
          >
            {loading ? (
              <span className="loading-spinner"></span>
            ) : (
              <span className="send-icon">→</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default RootApp;
