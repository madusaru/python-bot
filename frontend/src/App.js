import { useState, useEffect } from "react";
import "./styles.css";
import * as marked from "marked";

// 🔴 CHANGE THIS to your REAL Render backend URL
const API_BASE = "https://python-bot-2-ppir.onrender.com";

function App() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [useLora, setUseLora] = useState(true);

  // Load chat history
  useEffect(() => {
    fetch(`${API_BASE}/history`)
      .then((res) => res.json())
      .then((data) => setMessages(data))
      .catch((err) => console.log("History fetch error:", err));
  }, []);

  // Send message
  const sendMessage = async (msgText) => {
    const msg = msgText || input;

    if (!msg.trim() || isLoading) return;

    setInput("");
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "user", content: msg }]);

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

      setMessages((prev) => [
        ...prev,
        { role: "bot", content: data.response || "No response" },
      ]);

      if (data.history) setHistory(data.history);

    } catch (err) {
      setMessages((prev) => [
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

  return (
    <div>
      <header>
        <div className="logo">
          <div className="logo-icon">&gt;_</div>
          PythonBot
        </div>

        <div className="header-right">
          <button className="btn-clear" onClick={clearChat}>
            Clear chat
          </button>
        </div>
      </header>

      <main>
        <div className="chat-container">
          <div className="messages">

            {messages.length === 0 && (
              <div className="welcome">
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
                        __html: marked.parse(msg.content || ""),
                      }}
                    />
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="msg bot">
                <div className="avatar">PB</div>
                <div className="bubble">Typing...</div>
              </div>
            )}

          </div>

          <div className="input-area">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Ask me anything..."
            />

            <button onClick={() => sendMessage()}>
              Send
            </button>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;
