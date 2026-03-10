// EXCON Panel Component
// MEL/MIL (Inject) System control panel for white cell operators

'use client';

import { useState, useEffect, useCallback } from 'react';
import API from './api';

interface Inject {
  id: string;
  name: string;
  description: string;
  type: string;
  timing: string;
  status: string;
  conditions: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  effects: Array<{
    target: string;
    modifier: number;
    duration_turns?: number;
    description: string;
  }>;
  observations: Array<{
    item: string;
    expected_response: string;
    evaluation_criteria: string;
  }>;
  evaluation_points: number;
  difficulty: string;
  triggered_turn?: number;
}

interface InjectLog {
  id: string;
  inject_id: string;
  game_id: number;
  turn: number;
  timestamp: string;
  trigger_type: string;
  effects_applied: Record<string, unknown>[];
  results: Record<string, unknown>;
}

interface ExconPanelProps {
  gameId: number;
  turn: number;
  isWhiteCell?: boolean;
}

export default function ExconPanel({ gameId, turn, isWhiteCell = true }: ExconPanelProps) {
  const [injects, setInjects] = useState<Inject[]>([]);
  const [activeEffects, setActiveEffects] = useState<InjectLog[]>([]);
  const [injectHistory, setInjectHistory] = useState<InjectLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedInject, setSelectedInject] = useState<Inject | null>(null);

  // Fetch inject data
  const fetchInjects = useCallback(async () => {
    if (!isWhiteCell) return;

    try {
      const response = await fetch(`${API.baseUrl}/api/injects/${gameId}`);
      if (response.ok) {
        const data = await response.json();
        setInjects(data.injects || []);
        setActiveEffects(data.active_effects || []);
        setInjectHistory(data.history || []);
      }
    } catch (err) {
      console.error('Failed to fetch injects:', err);
    }
  }, [gameId, isWhiteCell]);

  useEffect(() => {
    fetchInjects();
  }, [fetchInjects]);

  // Trigger immediate inject
  const handleTriggerInject = async (injectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API.baseUrl}/api/injects/${gameId}/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inject_id: injectId,
          turn: turn,
          trigger_type: 'immediate'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setInjectHistory(prev => [result, ...prev]);
        await fetchInjects();
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to trigger inject');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  // Cancel inject
  const handleCancelInject = async (injectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API.baseUrl}/api/injects/${gameId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inject_id: injectId })
      });

      if (response.ok) {
        await fetchInjects();
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to cancel inject');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  // Reset inject
  const handleResetInject = async (injectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API.baseUrl}/api/injects/${gameId}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inject_id: injectId })
      });

      if (response.ok) {
        await fetchInjects();
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to reset inject');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  if (!isWhiteCell) {
    return null;
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-400';
      case 'medium': return 'text-yellow-400';
      case 'hard': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getTimingIcon = (timing: string) => {
    switch (timing) {
      case 'immediate': return '⚡';
      case 'conditional': return '🔄';
      case 'scheduled': return '📅';
      default: return '📋';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'available':
        return <span className="px-2 py-1 text-xs bg-green-900 text-green-300 rounded">Available</span>;
      case 'triggered':
        return <span className="px-2 py-1 text-xs bg-blue-900 text-blue-300 rounded">Triggered</span>;
      case 'expired':
        return <span className="px-2 py-1 text-xs bg-gray-700 text-gray-400 rounded">Expired</span>;
      case 'cancelled':
        return <span className="px-2 py-1 text-xs bg-red-900 text-red-300 rounded">Cancelled</span>;
      default:
        return <span className="px-2 py-1 text-xs bg-gray-700 text-gray-400 rounded">{status}</span>;
    }
  };

  const availableInjects = injects.filter(i => i.status === 'available');
  const triggeredInjects = injects.filter(i => i.status === 'triggered');

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 w-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>🎯</span> EXCON Panel (MEL/MIL)
        </h2>
        <span className="text-sm text-gray-400">Turn {turn}</span>
      </div>

      {error && (
        <div className="mb-4 p-2 bg-red-900/50 border border-red-700 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Active Effects */}
      {activeEffects.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-yellow-400 mb-2">Active Effects</h3>
          <div className="space-y-2">
            {activeEffects.map((log, idx) => (
              <div key={idx} className="p-2 bg-blue-900/30 border border-blue-700 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-blue-300 font-medium">{log.inject_id}</span>
                    <span className="text-gray-400 text-sm ml-2">Turn {log.turn}</span>
                  </div>
                  <span className="text-xs text-blue-400">{log.trigger_type}</span>
                </div>
                {log.effects_applied?.map((effect: Record<string, unknown>, i: number) => (
                  <div key={i} className="text-sm text-gray-300 mt-1">
                    {String(effect.target)}: {Number(effect.modifier) > 0 ? '+' : ''}{String(effect.modifier)}
                    {effect.duration_turns ? <span> ({String(effect.duration_turns)} turns)</span> : null}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Injects */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-green-400 mb-2">
          Available Injects ({availableInjects.length})
        </h3>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {availableInjects.map(inject => (
            <div
              key={inject.id}
              className={`p-2 bg-gray-800 border border-gray-700 rounded cursor-pointer hover:border-gray-500 transition-colors ${
                selectedInject?.id === inject.id ? 'border-blue-500' : ''
              }`}
              onClick={() => setSelectedInject(selectedInject?.id === inject.id ? null : inject)}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getTimingIcon(inject.timing)}</span>
                  <span className="text-white font-medium">{inject.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs ${getDifficultyColor(inject.difficulty)}`}>
                    {inject.difficulty}
                  </span>
                  <span className="text-xs text-gray-500">{inject.evaluation_points}pts</span>
                </div>
              </div>
              {selectedInject?.id === inject.id && (
                <div className="mt-2 pt-2 border-t border-gray-700">
                  <p className="text-sm text-gray-400 mb-2">{inject.description}</p>
                  <div className="text-xs text-gray-500 mb-2">
                    <div>Type: {inject.type}</div>
                    <div>Timing: {inject.timing}</div>
                  </div>
                  {inject.effects.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-gray-500 mb-1">Effects:</div>
                      {inject.effects.map((effect, i) => (
                        <div key={i} className="text-sm text-gray-300 ml-2">
                          • {effect.description}
                        </div>
                      ))}
                    </div>
                  )}
                  {inject.observations.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-gray-500 mb-1">Observations:</div>
                      {inject.observations.map((obs, i) => (
                        <div key={i} className="text-sm text-gray-300 ml-2">
                          • {obs.item}: {obs.expected_response}
                        </div>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTriggerInject(inject.id);
                    }}
                    disabled={loading}
                    className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-sm rounded transition-colors"
                  >
                    Trigger Now
                  </button>
                </div>
              )}
            </div>
          ))}
          {availableInjects.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-2">No available injects</div>
          )}
        </div>
      </div>

      {/* Triggered Injects */}
      {triggeredInjects.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-blue-400 mb-2">
            Triggered ({triggeredInjects.length})
          </h3>
          <div className="space-y-2">
            {triggeredInjects.map(inject => (
              <div key={inject.id} className="p-2 bg-gray-800 border border-gray-700 rounded">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-white">{inject.name}</span>
                    <span className="text-gray-500 text-sm ml-2">
                      Turn {inject.triggered_turn}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleResetInject(inject.id)}
                      disabled={loading}
                      className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-gray-300 text-xs rounded"
                    >
                      Reset
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      {injectHistory.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            History ({injectHistory.length})
          </h3>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {injectHistory.slice(0, 10).map((log, idx) => (
              <div key={idx} className="text-xs text-gray-500 flex justify-between">
                <span>
                  <span className="text-gray-400">T{log.turn}:</span> {log.inject_id}
                </span>
                <span className="text-gray-600">{log.trigger_type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
