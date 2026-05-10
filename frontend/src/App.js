import { useState, useEffect } from "react";
import "./styles.css";
import { marked } from "marked";

const API_BASE = "https://YOUR-RENDER-BACKEND.onrender.com";

function App() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [useLora, setUseLora] = useState(true);

  // Load chat history on page load
  useEffect(() => {
    fetch(`${API_BASE}/history`)
      .then(res => res.json())
      .then(data => setMessages(data))
      .catch(err => console.log("History fetch error:", err));
  }, []);

  // Send message
  const sendMessage = async (msgText) => {
    const msg = msgText || input;

    if (!msg.trim() || isLoading) return;

    setInput("");
    setIsLoading(true);

    // show user message instantly
    setMessages(prev => [...prev, { role: "user", content: msg }]);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg,
          history: history,
          use_lora: useLora,
        }),
      });

      const data = await res.json();

      // show bot response
      setMessages(prev => [
        ...prev,
        { role: "bot", content: data.response || "No response" },
      ]);

      if (data.history) setHistory(data.history);

    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: "bot", content: "Error: " + err.message },
      ]);
    }

    setIsLoading(false);
  };

  const clearChat = () => {
    setMessages([]);
    setHistory([]);
  };

  const topics = [
    "Variables & data types",
    "Lists & tuples",
    "Dictionaries",
    "Functions & scope",
    "OOP & classes",
    "List comprehensions",
    "File handling",
    "Error handling",
    "Decorators",
    "Generators",
    "Async / await",
    "pip & packages",
  ];

  return (
    <div>
      {/* HEADER */}
      <header>
        <div className="logo">
          <div className="logo-icon">&gt;_</div>
          PythonBot
        </div>

        <div className="header-right">
          <div className="mode-toggle">
            <span>LoRA</span>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={useLora}
                onChange={() => setUseLora(!useLora)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <button className="btn-clear" onClick={clearChat}>
            Clear chat
          </button>
        </div>
      </header>

      {/* MAIN */}
      <main>
        {/* SIDEBAR */}
        <aside className="sidebar">
          <div className="sidebar-label">Quick Topics</div>

          {topics.map((t, i) => (
            <button
              key={i}
              className="topic-btn"
              onClick={() => sendMessage(`Explain ${t} in Python with examples.`)}
            >
              <span className="dot"></span>
              {t}
            </button>
          ))}
        </aside>

        {/* CHAT */}
        <div className="chat-container">
          <div className="messages">

            {messages.length === 0 && (
              <div className="welcome">
                <div className="welcome-icon">&gt;_</div>
                <h1>Hey, I'm PythonBot 🐍</h1>
                <p>Your personal Python tutor.</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`msg ${msg.role}`}>
                <div className="avatar">
                  {msg.role === "user" ? "U" : "PB"}
                </div>

                <div className="bubble">
                  {msg.role === "bot" ? (
                    <div
                      dangerouslySetInnerHTML={{
                        __html: marked.parse(msg.content),
                      }}
                    />
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}

            {/* LOADING */}
            {isLoading && (
              <div className="msg bot">
                <div className="avatar">PB</div>
                <div className="bubble">
                  <div className="typing">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* INPUT */}
          <div className="input-area">
            <div className="input-wrap">
              <textarea
                className="input-box"
                placeholder="Ask me anything about Python…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />

              <button
                className="send-btn"
                onClick={() => sendMessage()}
                disabled={isLoading}
              >
                <svg viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>

            <div className="input-meta">
              <span>Model ready</span>
              <span>Enter to send</span>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;