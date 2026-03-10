"use client";

import { useState, useEffect, useRef } from "react";
import { useI18n } from "../lib/i18n";
import API from "../lib/api";

interface ChatMessage {
  id: number;
  game_id: number;
  user_id: number;
  username: string;
  content: string;
  channel: string;
  created_at: string;
  turn: number | null;
}

interface ChatPanelProps {
  gameId: number;
  userRole?: string;
}

export default function ChatPanel({ gameId, userRole = "observer" }: ChatPanelProps) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [selectedChannel, setSelectedChannel] = useState("all");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Available channels based on role
  const availableChannels = ["all"];
  if (userRole === "blue" || userRole === "admin" || userRole === "white") {
    availableChannels.push("commander");
  }
  if (userRole === "red" || userRole === "admin" || userRole === "white") {
    availableChannels.push("staff");
  }
  if (userRole === "admin" || userRole === "white") {
    availableChannels.push("excon");
    availableChannels.push("excon_announce");
  }
  if (userRole === "observer" || userRole === "admin" || userRole === "white") {
    availableChannels.push("observer");
  }

  const channelLabels: Record<string, string> = {
    all: t("chat.all") || "All",
    commander: t("chat.commander") || "Commander",
    staff: t("chat.staff") || "Staff",
    excon: t("chat.excon") || "EXCON",
    excon_announce: t("chat.exconAnnounce") || "EXCON Announce",
    white: t("chat.white") || "WHITE",
    observer: t("chat.observer") || "Observer",
  };

  const fetchMessages = async () => {
    if (!gameId) return;
    try {
      const res = await fetch(`${API.baseUrl}/api/games/${gameId}/chat?limit=50`);
      const data: { messages?: ChatMessage[] } = await res.json();
      if (data.messages) {
        setMessages(data.messages.reverse());
      }
    } catch (err) {
      console.error("Failed to fetch messages:", err);
    }
  };

  useEffect(() => {
    fetchMessages();
    // Poll for new messages every 5 seconds
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, [gameId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !gameId) return;

    setLoading(true);
    try {
      const res = await fetch(`${API.baseUrl}/api/games/${gameId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: newMessage,
          channel: selectedChannel,
        }),
      });

      if (res.ok) {
        setNewMessage("");
        await fetchMessages();
      }
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setLoading(false);
    }
  };

  const getChannelColor = (channel: string) => {
    const colors: Record<string, string> = {
      all: "bg-gray-600",
      commander: "bg-blue-600",
      staff: "bg-red-600",
      excon: "bg-yellow-600",
      excon_announce: "bg-orange-600",
      white: "bg-white-600",
      observer: "bg-purple-600",
    };
    return colors[channel] || "bg-gray-600";
  };

  // Filter messages by selected channel
  const filteredMessages = messages.filter((m) => {
    if (selectedChannel === "all") {
      // Show messages from selected channel's visible channels
      if (userRole === "blue") {
        return m.channel === "all" || m.channel === "commander";
      }
      if (userRole === "red") {
        return m.channel === "all" || m.channel === "staff";
      }
      if (userRole === "observer") {
        return m.channel === "all" || m.channel === "observer";
      }
      if (userRole === "white" || userRole === "admin") {
        return true; // Show all channels to EXCON/admin
      }
      return m.channel === "all" || m.channel === selectedChannel;
    }
    return m.channel === selectedChannel;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Channel selector */}
      <div className="flex gap-1 mb-2 flex-wrap">
        {availableChannels.map((channel) => (
          <button
            key={channel}
            onClick={() => setSelectedChannel(channel)}
            className={`px-2 py-1 rounded text-xs font-medium ${
              selectedChannel === channel
                ? `${getChannelColor(channel)} text-white`
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {channelLabels[channel]}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-2 mb-2 min-h-0">
        {filteredMessages.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">
            {t("chat.noMessages") || "No messages"}
          </p>
        ) : (
          filteredMessages.map((msg) => (
            <div
              key={msg.id}
              className="bg-gray-800 rounded p-2 text-sm"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-gray-300">{msg.username}</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-xs ${getChannelColor(msg.channel)} text-white`}
                >
                  {channelLabels[msg.channel] || msg.channel}
                </span>
                {msg.turn && (
                  <span className="text-xs text-gray-500">
                    T{msg.turn}
                  </span>
                )}
              </div>
              <p className="text-gray-300 break-words">{msg.content}</p>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="flex gap-2">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder={t("chat.placeholder") || "Type a message..."}
          className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
          maxLength={2000}
        />
        <button
          type="submit"
          disabled={loading || !newMessage.trim()}
          className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm font-medium disabled:opacity-50"
        >
          {t("chat.send") || "Send"}
        </button>
      </form>
    </div>
  );
}
