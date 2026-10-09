"use client";

import { useState, useRef, useEffect, useEffectEvent, Suspense } from "react";
import { useSearchParams } from "next/navigation";

type Message = {
  id: string;
  sender: "user" | "bot";
  text: string;
  intent?: string;
  toolsUsed?: string[];
  latency?: number;
  timestamp: string;
};

const CHAT_STORAGE_KEY = "ai-assistant-chat-messages";

function createWelcomeMessage(): Message {
  return {
    id: "init",
    sender: "bot",
    text: "👋 Hello! I am your AI Smart Event Assistant powered by Llama.\n\nYou can ask me to:\n• **Check Venues:** 'What are the venues available?'\n• **Upcoming Events:** 'What are the upcoming events?'\n• **Create & Book:** 'Create event AI Workshop on 2026-10-25 at venue 1 with 40 seats'\n• **Check Policies (RAG):** 'What is the cancellation and refund policy?'",
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }),
  };
}

function isMessage(value: unknown): value is Message {
  if (typeof value !== "object" || value === null) return false;
  const message = value as Record<string, unknown>;
  return (
    typeof message.id === "string" &&
    (message.sender === "user" || message.sender === "bot") &&
    typeof message.text === "string" &&
    typeof message.timestamp === "string"
  );
}

function AIAssistantChat() {
  const searchParams = useSearchParams();
  const initialPrompt = searchParams ? searchParams.get("prompt") || "" : "";

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoaded, setMessagesLoaded] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const storedMessages = localStorage.getItem(CHAT_STORAGE_KEY);
      if (storedMessages) {
        const parsedMessages: unknown = JSON.parse(storedMessages);
        if (Array.isArray(parsedMessages) && parsedMessages.every(isMessage)) {
          const welcomeMessage = createWelcomeMessage();
          const hasWelcomeMessage = parsedMessages.some((message) => message.id === "init");
          const restoredMessages = hasWelcomeMessage
            ? parsedMessages.map((message) =>
                message.id === "init" ? { ...message, text: welcomeMessage.text } : message
              )
            : [welcomeMessage, ...parsedMessages];
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setMessages(restoredMessages);
          setMessagesLoaded(true);
          return;
        }
      }
    } catch {
      // Fall back to the welcome message when stored data is unavailable.
    }

    setMessages([createWelcomeMessage()]);
    setMessagesLoaded(true);
  }, []);

  useEffect(() => {
    if (!messagesLoaded) return;
    try {
      localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // Keep the in-memory conversation usable if storage is unavailable.
    }
  }, [messages, messagesLoaded]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const clearChat = () => {
    localStorage.removeItem(CHAT_STORAGE_KEY);
    setMessages([createWelcomeMessage()]);
  };

  const sendMessage = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: String(Date.now()),
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const token = localStorage.getItem("access_token");
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token || ""}`,
        },
        body: JSON.stringify({ message: textToSend }),
      });

      if (!res.ok) {
        throw new Error("Chat request failed");
      }

      const data = await res.json();
      const botMsg: Message = {
        id: String(Date.now() + 1),
        sender: "bot",
        text: data.response || "No response received.",
        intent: data.intent,
        toolsUsed: data.tools_used,
        latency: data.latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const errorMsg: Message = {
        id: String(Date.now() + 1),
        sender: "bot",
        text: "⚠️ Could not connect to the AI Agent backend. Please verify that the FastAPI backend server is running on port 8000.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const sendInitialPrompt = useEffectEvent((prompt: string) => {
    if (!messagesLoaded || messages.some((message) => message.sender === "user" && message.text === prompt)) {
      return;
    }
    void sendMessage(prompt);
  });

  useEffect(() => {
    // The URL prompt is an external command that intentionally starts a chat request.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (initialPrompt.trim()) sendInitialPrompt(initialPrompt);
  }, [initialPrompt]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)] bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-4 px-6 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-slate-50 to-indigo-50/30">
        <h1 className="font-bold text-slate-900 text-base">Agentic AI Assistant</h1>
        <button
          type="button"
          onClick={clearChat}
          disabled={loading}
          className="text-xs font-medium text-slate-600 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Clear Chat
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 p-6 overflow-y-auto space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === "user";

          return (
            <div
              key={m.id}
              className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-sm leading-relaxed whitespace-pre-wrap ${
                  isUser
                    ? "bg-indigo-600 text-white rounded-br-xs shadow-xs"
                    : "bg-slate-100/90 text-slate-800 rounded-bl-xs border border-slate-200/60"
                }`}
              >
                {m.text}
              </div>

              <span className="text-[10px] text-slate-400 mt-1 px-1">
                {m.timestamp}
              </span>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-indigo-600 bg-indigo-50/80 p-3 rounded-xl w-fit">
            <span className="animate-spin text-base">⚙️</span>
            <span>Agent thinking & executing tools via Llama...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Bar */}
      <div className="p-4 border-t border-slate-200 bg-white flex items-center gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask AI: 'What venues are available?', 'Create event...', 'Cancellation policy?'"
          className="flex-1 bg-slate-100 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 outline-hidden focus:border-indigo-500 focus:bg-white transition"
          disabled={loading}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition shadow-xs flex items-center gap-2"
        >
          <span>Send</span>
          <span>➤</span>
        </button>
      </div>
    </div>
  );
}

export default function AIAssistantPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-slate-400">Loading AI Assistant...</div>}>
      <AIAssistantChat />
    </Suspense>
  );
}

