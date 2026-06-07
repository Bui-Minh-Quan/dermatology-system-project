import { useState, useEffect, useRef } from "react";
import api from "../api";
import "./chatbot.css";

export default function Chatbot() {
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const chatWindowRef = useRef(null);
  const messageInputRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);

  // Cuộn trong chính khung chat để tránh kéo giật cả trang.
  const scrollToBottom = () => {
    const container = chatWindowRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  };

  const handleChatScroll = () => {
    const container = chatWindowRef.current;
    if (!container) return;

    const distanceToBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    shouldAutoScrollRef.current = distanceToBottom < 90;
  };

  useEffect(() => {
    if (!chatLog.length) {
      const container = chatWindowRef.current;
      if (container) {
        container.scrollTop = 0;
      }
      return;
    }

    if (shouldAutoScrollRef.current) {
      scrollToBottom();
    }
  }, [chatLog]);

  useEffect(() => {
    const input = messageInputRef.current;
    if (!input) return;

    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  }, [message]);

  // Load lịch sử chat khi vừa vào trang
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await api.get("/chatbot/history");
        setChatLog(response.data.messages || []);
      } catch (error) {
        console.error("Failed to load chat history:", error);
      }
    };
    fetchHistory();
  }, []);

  // Gửi tin nhắn và nhận stream
  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim() || isStreaming) return;

    const userMsg = message.trim();
    setMessage("");
    shouldAutoScrollRef.current = true;

    // Cập nhật UI: Thêm tin nhắn user và 1 tin nhắn rỗng của AI để chờ nhận stream
    setChatLog((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      { role: "ai", content: "" },
    ]);

    setIsStreaming(true);
    const token = localStorage.getItem("access_token");

    try {
      // Dùng fetch thay vì axios vì axios hỗ trợ streaming dạng byte chưa tốt bằng fetch native API
      const response = await fetch("http://localhost:8000/chatbot/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!response.ok) throw new Error("Network response was not ok");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // Cập nhật liên tục vào tin nhắn cuối cùng (tin nhắn của AI)
        setChatLog((prev) => {
          const newLog = [...prev];
          const lastIndex = newLog.length - 1;
          newLog[lastIndex] = {
            ...newLog[lastIndex],
            content: newLog[lastIndex].content + chunk,
          };
          return newLog;
        });
      }
    } catch (error) {
      console.error("Chat request failed:", error);
      setChatLog((prev) => [
        ...prev,
        { role: "ai", content: "Sorry, the AI service connection failed. Please try again." },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleInputKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!message.trim() || isStreaming) return;
      handleSend(e);
    }
  };

  // Xóa lịch sử chat
  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to delete the entire chat history?")) return;
    
    try {
      await api.delete("/chatbot/history");
      setChatLog([]);
    } catch (error) {
      console.error("Failed to clear chat history:", error);
      alert("Unable to clear chat history right now.");
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <h2>🤖 Medical Assistant</h2>
        <button onClick={handleClearHistory} className="clear-btn" title="Clear history">
          🗑️
        </button>
      </div>

      <div className="chat-window" ref={chatWindowRef} onScroll={handleChatScroll}>
        {chatLog.length === 0 ? (
          <div className="empty-state">
            <p>Hello! How can I help you today?</p>
          </div>
        ) : (
          chatLog.map((msg, index) => (
            <div key={index} className={`message-wrapper ${msg.role}`}>
              <div className="message-bubble">
                {msg.content}
              </div>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <textarea
          ref={messageInputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleInputKeyDown}
          placeholder="Type your question..."
          disabled={isStreaming}
          className="chat-input"
          rows={1}
        />
        <button type="submit" disabled={isStreaming || !message.trim()} className="send-btn">
          Send
        </button>
      </form>
    </div>
  );
}