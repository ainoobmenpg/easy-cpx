"use client";

import { useState, useEffect } from "react";
import { useI18n } from "../lib/i18n";
import LanguageSwitcher from "../lib/language-switcher";
import { ConnectionBadge, DiagnosticModal, checkConnection, ConnectionState } from "../lib/connection-indicator";
import API from "../lib/api";

interface ReplayEvent {
  turn: number;
  type: string;
  time?: string;
  weather?: string;
  attacker?: string;
  defender?: string;
  outcome?: string;
  unit_id?: number;
  from?: { x: number; y: number };
  to?: { x: number; y: number };
  inject_type?: string;
  trigger?: string;
  summary?: string;
}

interface ReplayTimeline {
  seed: number;
  turn_seeds: Record<number, number>;
  total_turns: number;
  events: ReplayEvent[];
}

export default function ReplayViewer() {
  const { t } = useI18n();
  const [gameId, setGameId] = useState<number>(1);
  const [timeline, setTimeline] = useState<ReplayTimeline | null>(null);
  const [currentTurn, setCurrentTurn] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diagnosticOpen, setDiagnosticOpen] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>({ status: 'unknown' });

  const loadTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(API.replayTimeline(gameId));
      const data = await res.json();
      if (data.detail) {
        setError(data.detail);
      } else {
        setTimeline(data);
        setCurrentTurn(data.total_turns || 1);
      }
    } catch (err) {
      setError("Failed to load replay data");
    } finally {
      setLoading(false);
    }
  };

  // Check connection status on mount
  useEffect(() => {
    (async () => {
      const result = await checkConnection();
      setConnectionState(result);
    })();
  }, []);

  const handleRetry = async () => {
    const result = await checkConnection();
    setConnectionState(result);
  };

  const getEventsByTurn = (turn: number) => {
    if (!timeline) return [];
    return timeline.events.filter((e) => e.turn === turn);
  };

  const getEventTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      turn_start: t("replay.turnStart") || "Turn Start",
      turn_end: t("replay.turnEnd") || "Turn End",
      combat: t("replay.combat") || "Combat",
      movement: t("replay.movement") || "Movement",
      inject: t("replay.inject") || "Inject",
      sitrep: t("replay.sitrep") || "SITREP",
    };
    return labels[type] || type;
  };

  const getEventTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      turn_start: "bg-blue-600",
      turn_end: "bg-gray-600",
      combat: "bg-red-600",
      movement: "bg-green-600",
      inject: "bg-purple-600",
      sitrep: "bg-yellow-600",
    };
    return colors[type] || "bg-gray-600";
  };

  const getOutcomeColor = (outcome: string) => {
    const colors: Record<string, string> = {
      success: "text-green-400",
      partial: "text-yellow-400",
      failed: "text-red-400",
      blocked: "text-gray-400",
    };
    return colors[outcome] || "text-gray-400";
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">
              {t("replay.title") || "Replay Viewer"}
            </h1>
            <p className="text-gray-400 mt-2">
              {t("replay.subtitle") || "Review game events with full timeline"}
            </p>
          </div>
          <ConnectionBadge onClick={() => setDiagnosticOpen(true)} />
          <LanguageSwitcher />
        </header>

        {/* Load Replay Form */}
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">
            {t("replay.loadGame") || "Load Game Replay"}
          </h2>
          <div className="flex gap-4 items-center">
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                {t("replay.gameId") || "Game ID"}
              </label>
              <input
                type="number"
                value={gameId}
                onChange={(e) => setGameId(Number(e.target.value))}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 w-32"
              />
            </div>
            <button
              onClick={loadTimeline}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-medium mt-5 disabled:opacity-50"
            >
              {loading
                ? t("replay.loading") || "Loading..."
                : t("replay.load") || "Load Replay"}
            </button>
          </div>
          {error && <p className="text-red-400 mt-3">{error}</p>}
        </div>

        {/* Timeline Display */}
        {timeline && (
          <>
            {/* Replay Controls */}
            <div className="bg-gray-900 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setCurrentTurn(Math.max(1, currentTurn - 1))}
                    disabled={currentTurn <= 1}
                    className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded disabled:opacity-50"
                  >
                    ← Prev
                  </button>
                  <div className="text-xl font-bold">
                    {t("replay.turn") || "Turn"} {currentTurn} / {timeline.total_turns}
                  </div>
                  <button
                    onClick={() =>
                      setCurrentTurn(Math.min(timeline.total_turns, currentTurn + 1))
                    }
                    disabled={currentTurn >= timeline.total_turns}
                    className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded disabled:opacity-50"
                  >
                    Next →
                  </button>
                </div>
                <div className="text-gray-400">
                  {t("replay.seed") || "Seed"}: {timeline.seed}
                </div>
              </div>

              {/* Turn Slider */}
              <input
                type="range"
                min={1}
                max={timeline.total_turns}
                value={currentTurn}
                onChange={(e) => setCurrentTurn(Number(e.target.value))}
                className="w-full mt-4"
              />
            </div>

            {/* Turn Navigation */}
            <div className="flex gap-2 mb-6 flex-wrap">
              {Array.from({ length: timeline.total_turns }, (_, i) => i + 1).map(
                (turn) => (
                  <button
                    key={turn}
                    onClick={() => setCurrentTurn(turn)}
                    className={`px-3 py-1 rounded text-sm ${
                      turn === currentTurn
                        ? "bg-blue-600 text-white"
                        : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                    }`}
                  >
                    T{turn}
                  </button>
                )
              )}
            </div>

            {/* Events for Current Turn */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                {t("replay.events") || "Events"} -{" "}
                {t("replay.turn") || "Turn"} {currentTurn}
              </h3>

              {getEventsByTurn(currentTurn).length === 0 ? (
                <p className="text-gray-500">{t("replay.noEvents") || "No events"}</p>
              ) : (
                <div className="space-y-3">
                  {getEventsByTurn(currentTurn).map((event, idx) => (
                    <div
                      key={idx}
                      className="bg-gray-800 rounded-lg p-4 border-l-4"
                      style={{
                        borderColor:
                          event.type === "combat"
                            ? "#ef4444"
                            : event.type === "movement"
                            ? "#22c55e"
                            : event.type === "inject"
                            ? "#a855f7"
                            : event.type === "sitrep"
                            ? "#eab308"
                            : "#6b7280",
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <span
                            className={`px-2 py-1 rounded text-xs ${getEventTypeColor(
                              event.type
                            )}`}
                          >
                            {getEventTypeLabel(event.type)}
                          </span>
                          {event.time && (
                            <span className="text-gray-400 text-sm">{event.time}</span>
                          )}
                          {event.weather && (
                            <span className="text-gray-400 text-sm">
                              {event.weather}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Combat Details */}
                      {event.type === "combat" && (
                        <div className="mt-2 text-sm">
                          <span className="text-red-400">{event.attacker}</span>
                          {" vs "}
                          <span className="text-blue-400">{event.defender}</span>
                          {" → "}
                          <span className={getOutcomeColor(event.outcome || "")}>
                            {event.outcome}
                          </span>
                        </div>
                      )}

                      {/* Movement Details */}
                      {event.type === "movement" && (
                        <div className="mt-2 text-sm">
                          <span className="text-gray-400">Unit {event.unit_id}</span>
                          {event.from && event.to && (
                            <span className="text-gray-400">
                              {" "}
                              ({event.from.x},{event.from.y}) → ({event.to.x},{event.to.y})
                            </span>
                          )}
                        </div>
                      )}

                      {/* Inject Details */}
                      {event.type === "inject" && (
                        <div className="mt-2 text-sm">
                          <span className="text-purple-400">{event.inject_type}</span>
                          {event.trigger && (
                            <span className="text-gray-400"> - {event.trigger}</span>
                          )}
                        </div>
                      )}

                      {/* SITREP Summary */}
                      {event.type === "sitrep" && event.summary && (
                        <div className="mt-2 text-sm text-gray-300">
                          {event.summary}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Full Timeline */}
            <div className="bg-gray-900 rounded-lg p-6 mt-6">
              <h3 className="text-lg font-semibold mb-4">
                {t("replay.fullTimeline") || "Full Timeline"}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-2 px-3 text-gray-400">
                        {t("replay.turn") || "Turn"}
                      </th>
                      <th className="text-left py-2 px-3 text-gray-400">
                        {t("replay.type") || "Type"}
                      </th>
                      <th className="text-left py-2 px-3 text-gray-400">
                        {t("replay.details") || "Details"}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {timeline.events
                      .filter(
                        (e) =>
                          !["turn_start", "turn_end"].includes(e.type)
                      )
                      .map((event, idx) => (
                        <tr
                          key={idx}
                          className={`border-b border-gray-800 cursor-pointer hover:bg-gray-800 ${
                            event.turn === currentTurn ? "bg-gray-800" : ""
                          }`}
                          onClick={() => setCurrentTurn(event.turn)}
                        >
                          <td className="py-2 px-3">{event.turn}</td>
                          <td className="py-2 px-3">
                            <span
                              className={`px-2 py-1 rounded text-xs ${getEventTypeColor(
                                event.type
                              )}`}
                            >
                              {getEventTypeLabel(event.type)}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-gray-400">
                            {event.type === "combat" &&
                              `${event.attacker} vs ${event.defender} (${event.outcome})`}
                            {event.type === "movement" && `Unit ${event.unit_id}`}
                            {event.type === "inject" && event.inject_type}
                            {event.type === "sitrep" &&
                              (event.summary || "").substring(0, 50)}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
      <DiagnosticModal
        isOpen={diagnosticOpen}
        onClose={() => setDiagnosticOpen(false)}
        connectionState={connectionState}
        onRetry={handleRetry}
      />
    </div>
  );
}
