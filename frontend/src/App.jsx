import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [memories, setMemories] = useState([]);
  const [showMemories, setShowMemories] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  }, [messages, loading]);

  const loadMemories = async () => {
    try {
      const response = await fetch(`${API_URL}/memories`);
      const data = await response.json();

      setMemories(data.memories);
    } catch (error) {
      console.error("Failed to load memories:", error);
    }
  };

  const sendMessage = async () => {
    const trimmedInput = input.trim();

    if (!trimmedInput || loading) {
      return;
    }

    const userMessage = {
      role: "user",
      content: trimmedInput
    };

    const updatedMessages = [
      ...messages,
      userMessage
    ];

    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          messages: updatedMessages
        })
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data = await response.json();

      setMessages([
        ...updatedMessages,
        {
          role: "assistant",
          content: data.reply
        }
      ]);

      loadMemories();

    } catch (error) {
      console.error(error);

      setMessages([
        ...updatedMessages,
        {
          role: "assistant",
          content:
            "I'm having trouble connecting to my backend right now. 😭"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const deleteMemory = async (id) => {
    try {
      await fetch(`${API_URL}/memory/${id}`, {
        method: "DELETE"
      });

      loadMemories();
    } catch (error) {
      console.error("Failed to delete memory:", error);
    }
  };

  const newChat = () => {
    setMessages([]);
    setInput("");
  };

  return (
    <div className="app">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            ❤️
          </div>

          <div>
            <h1>Great Love</h1>
            <span>Personal AI</span>
          </div>
        </div>

        <button
          className="new-chat"
          onClick={newChat}
        >
          <span>＋</span>
          New Chat
        </button>

        <button
          className={`sidebar-button ${
            showMemories ? "active" : ""
          }`}
          onClick={() => {
            setShowMemories(!showMemories);
            loadMemories();
          }}
        >
          <span>🧠</span>
          Memories
        </button>

        <div className="sidebar-bottom">

          <div className="creator">
            <div className="creator-avatar">
              S
            </div>

            <div>
              <strong>Sibusiso</strong>
              <span>Creator</span>
            </div>
          </div>

        </div>

      </aside>


      {/* MAIN */}

      <main className="chat-area">

        {/* HEADER */}

        <header className="chat-header">

          <div className="assistant-info">

            <div className="assistant-avatar">
              ❤️
            </div>

            <div>
              <h2>Great Love</h2>

              <div className="online-status">
                <span className="status-dot"></span>
                Online
              </div>
            </div>

          </div>

          <div className="header-info">
            Local AI • Llama 3.2
          </div>

        </header>


        {/* MEMORY PANEL */}

        {showMemories ? (

          <section className="memory-panel">

            <div className="memory-panel-header">

              <div>
                <h2>🧠 Memories</h2>

                <p>
                  Things Great Love remembers about you.
                </p>
              </div>

              <button
                onClick={loadMemories}
                className="refresh-button"
              >
                ↻
              </button>

            </div>

            {memories.length === 0 ? (

              <div className="no-memories">

                <div>🧠</div>

                <h3>No memories yet</h3>

                <p>
                  Tell Great Love something about yourself.
                </p>

              </div>

            ) : (

              <div className="memory-list">

                {memories.map((memory) => (

                  <div
                    className="memory-card"
                    key={memory.id}
                  >

                    <div>

                      <span className="memory-category">
                        {memory.category}
                      </span>

                      <p>
                        {memory.memory}
                      </p>

                    </div>

                    <button
                      className="delete-memory"
                      onClick={() =>
                        deleteMemory(memory.id)
                      }
                    >
                      🗑️
                    </button>

                  </div>

                ))}

              </div>

            )}

          </section>

        ) : (

          <>

            {/* MESSAGES */}

            <section className="messages">

              {messages.length === 0 && (

                <div className="welcome-screen">

                  <div className="welcome-logo">
                    ❤️
                  </div>

                  <h2>
                    What can I help you with?
                  </h2>

                  <p>
                    I'm Great Love, your personal AI assistant.
                  </p>

                  <div className="suggestions">

                    <button
                      onClick={() =>
                        setInput(
                          "Tell me something interesting."
                        )
                      }
                    >
                      💡 Tell me something interesting
                    </button>

                    <button
                      onClick={() =>
                        setInput(
                          "Help me plan my day."
                        )
                      }
                    >
                      📅 Help me plan my day
                    </button>

                    <button
                      onClick={() =>
                        setInput(
                          "What do you remember about me?"
                        )
                      }
                    >
                      🧠 What do you remember?
                    </button>

                  </div>

                </div>

              )}


              {messages.map((message, index) => (

                <div
                  className={`message-row ${
                    message.role === "user"
                      ? "user-row"
                      : "assistant-row"
                  }`}
                  key={index}
                >

                  {message.role === "assistant" && (

                    <div className="message-avatar">
                      ❤️
                    </div>

                  )}

                  <div
                    className={`message-bubble ${
                      message.role === "user"
                        ? "user-bubble"
                        : "assistant-bubble"
                    }`}
                  >
                    {message.content}
                  </div>

                </div>

              ))}


              {loading && (

                <div className="message-row assistant-row">

                  <div className="message-avatar">
                    ❤️
                  </div>

                  <div className="assistant-bubble typing">

                    <span></span>
                    <span></span>
                    <span></span>

                  </div>

                </div>

              )}

              <div ref={messagesEndRef}></div>

            </section>


            {/* INPUT */}

            <div className="input-container">

              <div className="input-box">

                <textarea
                  value={input}
                  onChange={(event) =>
                    setInput(event.target.value)
                  }
                  onKeyDown={handleKeyDown}
                  placeholder="Message Great Love..."
                  rows="1"
                />

                <button
                  className="send-button"
                  onClick={sendMessage}
                  disabled={!input.trim() || loading}
                >
                  ↑
                </button>

              </div>

              <p className="input-hint">
                Great Love runs locally using Ollama •
                Enter to send
              </p>

            </div>

          </>

        )}

      </main>

    </div>
  );
}

export default App;