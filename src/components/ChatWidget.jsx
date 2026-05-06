import { useState } from "react";
import styles from "./ChatWidget.module.css";

const ChatWidget = ({ user_id }) => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);

  const toggleOpen = () => {
    setOpen((current) => !current);
  };

  const sendMessage = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || loading) return;

    const userMessage = { role: "user", content: trimmed };
    setMessages((current) => [...current, userMessage]);
    setInputValue("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_id, message: trimmed }),
      });

      const data = await response.json();
      const assistantMessage = {
        role: "assistant",
        content: data.reply || "Sorry, something went wrong.",
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: "assistant", content: "Unable to reach chat service." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={styles.container}>
      {open && (
        <div className={styles.panel}>
          <div className={styles.header}>
            <span>Chat with CLEAR-ai</span>
            <button className={styles.closeButton} onClick={toggleOpen}>
              ✕
            </button>
          </div>

          <div className={styles.messageList}>
            {messages.length === 0 && !loading ? (
              <div className={styles.emptyState}>
                Start the conversation by asking a question.
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={
                    message.role === "assistant"
                      ? styles.assistantBubble
                      : styles.userBubble
                  }
                >
                  {message.content}
                </div>
              ))
            )}
            {loading && (
              <div className={styles.loadingBubble}>...</div>
            )}
          </div>

          <div className={styles.inputArea}>
            <input
              className={styles.input}
              type="text"
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              disabled={loading}
            />
            <button
              className={styles.sendButton}
              onClick={sendMessage}
              disabled={loading || !inputValue.trim()}
            >
              Send
            </button>
          </div>
        </div>
      )}

      <button className={styles.fab} onClick={toggleOpen}>
        {open ? "Close chat" : "CLEAR-ai"}
      </button>
    </div>
  );
};

export default ChatWidget;
