'use client';

import { useState, useEffect, useRef, useMemo, useCallback, memo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

interface Unit {
  id: number;
  name: string;
  type: string;
  side: 'player' | 'enemy';
  x: number;
  y: number;
  status: string;
  ammo: string;
  fuel: string;
  readiness: string;
  strength: number;
  infantry_subtype?: string;
  recon_value?: number;
  visibility_range?: number;
  observation_confidence?: string;
  last_observed_turn?: number;
  // Extended reconnaissance fields
  confidence_score?: number;
  estimated_x?: number;
  estimated_y?: number;
  position_accuracy?: number;
  last_known_type?: string;
  observation_sources?: Array<{ observer_id: number; confidence: number }>;
}

interface GameState {
  game_id: number;
  turn: number;
  time: string;
  date: string;
  weather: string;
  phase: string;
  is_night: boolean;
  terrain: Record<string, string>;
  terrain_info: Record<string, { symbol: string; color: string; name: string }>;
  weather_effects: Record<string, any>;
  units: Unit[];
}

interface Sitrep {
  turn: number;
  sections: { type: string; content: string; confidence: string }[];
}

interface TurnLog {
  turn: number;
  orders: { unit: string; outcome: string }[];
}

// Memoized Unit component for performance
const UnitMarker = memo(function UnitMarker({
  unit,
  selectedUnitId,
  onSelect
}: {
  unit: Unit;
  selectedUnitId: number | null;
  onSelect: (unit: Unit) => void;
}) {
  const svgX = Math.floor(unit.x) + 0.5;
  const svgY = Math.floor(unit.y) + 0.5;
  const sideColor = unit.side === 'player' ? '#3b82f6' : '#ef4444';
  const isSelected = selectedUnitId === unit.id;

  // NATO symbol map
  const typeMap: Record<string, string> = {
    'nato_infantry': 'infantry', 'nato_armor': 'armor', 'nato_artillery': 'artillery',
    'nato_multirole': 'reconnaissance', 'nato_air_defense': 'air_defense', 'nato_uav': 'uav',
    'wp_infantry': 'infantry', 'wp_armor': 'armor', 'wp_artillery': 'artillery',
    'wp_air_defense': 'air_defense', 'wp_uav': 'uav', 'infantry': 'infantry', 'armor': 'armor',
    'artillery': 'artillery', 'reconnaissance': 'reconnaissance', 'air_defense': 'air_defense',
    'uav': 'uav',
  };
  const symbols: Record<string, string> = {
    infantry: '✕', armor: '⇒', artillery: '+', reconnaissance: '◇', air_defense: '▲', uav: '◈',
  };
  const symbol = symbols[typeMap[unit.type] || 'infantry'];

  // Status color
  const statusColors: Record<string, string> = {
    intact: '#22c55e', light_damage: '#eab308', medium_damage: '#f97316',
    heavy_damage: '#ef4444', destroyed: '#6b7280'
  };
  const statusColor = statusColors[unit.status] || '#22c55e';

  // Observation confidence styling for enemy units
  const isEnemy = unit.side === 'enemy';
  const confidence = unit.observation_confidence;
  const confidenceScore = unit.confidence_score;
  let confidenceOpacity = 1.0;
  let confidenceBorder = false;
  let confidenceLabel = '';
  if (isEnemy && confidence) {
    if (confidence === 'unknown') {
      confidenceOpacity = 0.5; // Unknown - more transparent
      confidenceBorder = true;
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : '?';
    } else if (confidence === 'estimated') {
      confidenceOpacity = 0.75; // Estimated - slightly transparent
      confidenceBorder = true;
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : '~';
    } else {
      // confirmed
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : 'OK';
    }
    // confirmed - fully opaque, no border
  }

  return (
    <g onClick={() => onSelect(unit)} style={{ cursor: 'pointer' }}>
      <rect x={svgX - 0.6} y={svgY - 0.5} width="1.2" height="1.0"
        fill={sideColor} stroke={isSelected ? '#fff' : (confidenceBorder ? '#fbbf24' : 'none')} strokeWidth="0.1" opacity={confidenceOpacity * 0.95}/>
      <text x={svgX} y={svgY + 0.2} fontSize="0.8" fill="#fff" textAnchor="middle" fontWeight="bold" opacity={confidenceOpacity}>
        {symbol}
      </text>
      <text x={svgX + 0.8} y={svgY + 0.8} fontSize="0.5" fill="#fff" stroke="#000" strokeWidth="0.15" paintOrder="stroke" fontWeight="bold" opacity={confidenceOpacity}>
        {unit.name}{confidenceLabel ? ` (${confidenceLabel})` : ''}
      </text>
      <rect x={svgX + 0.4} y={svgY + 0.4} width="0.3" height="0.2" fill={statusColor} stroke="#000" strokeWidth="0.05" opacity={confidenceOpacity}/>
    </g>
  );
});

function GameContent() {
  const searchParams = useSearchParams();
  const gameIdParam = searchParams.get('gameId');
  const router = useRouter();
  const [gameId] = useState(gameIdParam ? parseInt(gameIdParam, 10) : 1);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [sitrep, setSitrep] = useState<Sitrep | null>(null);
  const [orderInput, setOrderInput] = useState('');
  const [parsedOrder, setParsedOrder] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null);
  const [showHelp, setShowHelp] = useState(true);
  const [turnLogs, setTurnLogs] = useState<TurnLog[]>([]);
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState<string | null>(null);
  // Map pan state (for drag to pan)
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [didPan, setDidPan] = useState(false);  // Track if actual panning occurred
  const [terrainTooltip, setTerrainTooltip] = useState<{ x: number; y: number; terrain: string; info: { name: string; symbol: string; color: string } } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchGameState(); }, [gameId]);

  const fetchGameState = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/game/${gameId}/state`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGameState(data);
      setError(null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      console.error('Failed to fetch game state:', msg);
      setError(msg);
    }
  };

  const parseOrder = async () => {
    if (!orderInput.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/parse-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_input: orderInput, game_id: gameId })
      });
      const data = await res.json();
      setParsedOrder(data);
    } catch (e) { console.error('Failed to parse order:', e); }
    setLoading(false);
  };

  const submitOrder = async () => {
    if (!parsedOrder || !selectedUnit) return;
    setLoading(true);
    try {
      await fetch('http://localhost:8000/api/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unit_id: selectedUnit.id,
          order_type: parsedOrder.order_type,
          intent: parsedOrder.intent,
          location_x: parsedOrder.location?.x,
          location_y: parsedOrder.location?.y,
        })
      });
      setOrderInput('');
      setParsedOrder(null);
      setSelectedUnit(null);
      fetchGameState();
    } catch (e) { console.error('Failed to submit order:', e); }
    setLoading(false);
  };

  const advanceTurn = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/advance-turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId })
      });
      const data = await res.json();
      setSitrep(data.sitrep);
      setGameState(prev => prev ? { ...prev, turn: data.turn + 1, time: data.next_time } : null);

      // Refresh game state including units after turn advancement
      const stateRes = await fetch(`http://localhost:8000/api/game/${gameId}/state`);
      const stateData = await stateRes.json();
      setGameState(stateData);

      // Build log entries from player orders, enemy results, and events
      const logEntries: { unit: string; outcome: string }[] = [];

      // Add player order results
      (data.results || []).forEach((r: any) => {
        logEntries.push({
          unit: r.unit_name || `Unit ${r.order_id}`,
          outcome: r.outcome
        });
      });

      // Add enemy results
      (data.enemy_results || []).forEach((r: any) => {
        logEntries.push({
          unit: `[敵] ${r.unit_name || 'Unknown'}`,
          outcome: r.outcome || 'attack'
        });
      });

      // Add enemy activity events (movement toward player, attacks)
      (data.events || []).forEach((e: any) => {
        if (e.type === 'enemy_move' && e.target) {
          logEntries.push({
            unit: `[敵] ${e.unit_name || 'Unknown'}`,
            outcome: `→ ${e.target}`
          });
        } else if (e.type === 'enemy_attack_available') {
          logEntries.push({
            unit: `[敵] ${e.unit_name || 'Unknown'}`,
            outcome: 'attack_ready'
          });
        }
      });

      const newLog: TurnLog = {
        turn: data.turn,
        orders: logEntries,
      };
      setTurnLogs(prev => [newLog, ...prev]);
    } catch (e) { console.error('Failed to advance turn:', e); }
    setLoading(false);
  };

  const endGame = async () => {
    if (!confirm('End the game and view debriefing?')) return;
    try {
      await fetch('http://localhost:8000/api/game/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId })
      });
      router.push(`/debriefing?gameId=${gameId}`);
    } catch (e) {
      console.error('Failed to end game:', e);
    }
  };

  // Zoom with wheel
  const handleWheel = useCallback((e: React.WheelEvent) => {
    const delta = e.deltaY > 0 ? -0.2 : 0.2;
    setZoom(z => Math.max(0.5, Math.min(3, z + delta)));
  }, []);

  // Pan handlers - memoized
  const handlePanStart = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsPanning(true);
    setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    setDidPan(false);  // Reset pan flag
  }, [pan.x, pan.y]);

  const handlePan = useCallback((e: React.MouseEvent) => {
    if (!isPanning) return;
    setDidPan(true);  // Mark that we actually panned
    setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
  }, [isPanning, panStart.x, panStart.y]);

  const handlePanEnd = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Memoized zoom handlers
  const handleZoomIn = useCallback(() => setZoom(z => Math.min(3, z + 0.2)), []);
  const handleZoomOut = useCallback(() => setZoom(z => Math.max(0.5, z - 0.2)), []);
  const handleZoomReset = useCallback(() => { setZoom(1); setPan({ x: 0, y: 0 }); }, []);

  // Memoized grid lines as single path elements (was 124 line elements)
  const gridLines = useMemo(() => {
    // Minor grid lines (every 1 unit)
    let minorPath = '';
    for (let i = 0; i <= 50; i++) {
      minorPath += `M${i},0 V50 M0,${i} H50`;
    }
    // Major grid lines (every 5 units)
    let majorPath = '';
    for (let i = 0; i <= 50; i += 5) {
      majorPath += `M${i},0 V50 M0,${i} H50`;
    }
    return { minorPath, majorPath };
  }, []);

  // Memoized terrain data processing
  const terrainElements = useMemo(() => {
    if (!gameState?.terrain) return [];
    const terrainByGrid: Record<string, { key: string; terrainType: string }> = {};
    Object.entries(gameState.terrain).forEach(([key, terrainType]) => {
      const [x, y] = key.split(',').map(Number);
      const gridX = Math.floor(x);
      const gridY = Math.floor(y);
      const gridKey = `${gridX},${gridY}`;
      if (!terrainByGrid[gridKey] && terrainType !== 'plain') {
        terrainByGrid[gridKey] = { key, terrainType };
      }
    });
    return Object.values(terrainByGrid).map(({ key, terrainType }) => {
      const [x, y] = key.split(',').map(Number);
      const gridX = Math.floor(x);
      const gridY = Math.floor(y);
      const svgX = gridX + 0.5;
      const svgY = gridY + 0.5;
      const info = gameState.terrain_info?.[terrainType];
      if (!info) return null;
      return { key: `terrain-${key}`, svgX, svgY, gridX, gridY, terrainType, info };
    }).filter(Boolean);
  }, [gameState?.terrain, gameState?.terrain_info]);

  // Memoized unit select handler
  const handleUnitSelect = useCallback((unit: Unit) => {
    // Don't select unit if user was panning (dragging)
    if (didPan) return;
    setSelectedUnit(unit);
  }, [didPan]);

  // Memoized unit list for rendering
  const unitList = useMemo(() => gameState?.units || [], [gameState?.units]);

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { intact: '#22c55e', light_damage: '#eab308', medium_damage: '#f97316', heavy_damage: '#ef4444', destroyed: '#6b7280' };
    return colors[status] || '#22c55e';
  };
  const getSideColor = (side: string) => side === 'player' ? '#3b82f6' : '#ef4444';
  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = { intact: '無傷', light_damage: '軽損', medium_damage: '中損', heavy_damage: '大損', destroyed: '壊滅' };
    return labels[status] || status;
  };
  const getSupplyLabel = (level: string) => { const labels: Record<string, string> = { full: '満', depleted: '少', exhausted: '枯' }; return labels[level] || level; };
  const getOutcomeIcon = (outcome: string, unitName?: string) => {
    const icons: Record<string, string> = {
      success: '✅', partial: '⚠️', failed: '❌', blocked: '🚫', cancelled: '⏸️',
      attack: '⚔️', attack_ready: '🎯', move: '➡️'
    };
    // For enemy units, show different icons
    if (unitName && unitName.startsWith('[敵]')) {
      if (outcome === 'failed') return '💥';  // Enemy attack failed
      if (outcome === 'success') return '🔥';  // Enemy attack succeeded
      if (outcome === 'partial') return '⚡';  // Partial
      if (outcome === 'attack') return '⚔️';
      if (outcome === 'attack_ready') return '🎯';
    }
    // Check if outcome starts with "→ " (movement toward target)
    if (outcome && outcome.startsWith('→ ')) return '➡️';
    return icons[outcome] || '❓';
  };

  // NATO APP-6 symbol paths for unit types
  const getNatoSymbol = (unitType: string) => {
    // Map API unit types to symbol keys
    const typeMap: Record<string, string> = {
      'nato_infantry': 'infantry',
      'nato_armor': 'armor',
      'nato_artillery': 'artillery',
      'nato_multirole': 'reconnaissance',
      'nato_air_defense': 'air_defense',
      'wp_infantry': 'infantry',
      'wp_armor': 'armor',
      'wp_artillery': 'artillery',
      'wp_air_defense': 'air_defense',
      'infantry': 'infantry',
      'armor': 'armor',
      'artillery': 'artillery',
      'reconnaissance': 'reconnaissance',
      'air_defense': 'air_defense',
    };
    const mappedType = typeMap[unitType] || 'infantry';
    const symbols: Record<string, string> = {
      infantry: '✕',
      armor: '⇒',
      artillery: '+',
      reconnaissance: '◇',
      air_defense: '▲',
    };
    return symbols[mappedType] || '✕';
  };

  const getUnitTypeColor = (unitType: string) => {
    const colors: Record<string, string> = {
      infantry: '#fff',
      armor: '#fff',
      artillery: '#fff',
      combined_arms: '#fff',
      reconnaissance: '#fff',
      air_defense: '#fff',
    };
    return colors[unitType] || '#fff';
  };

  // Convert 50x50 coordinates to 20x10 grid display (expanded map)
  // terrain x,y (0-49) -> grid cell (0-49 for 50x50 map)
  const coordToGrid = (x: number, y: number) => ({
    gridX: Math.floor(x),
    gridY: Math.floor(y)
  });

  // Convert grid cell to SVG display
  const gridToSvg = (gridX: number, gridY: number) => ({
    x: gridX + 0.5,
    y: gridY + 0.5
  });

  // Convert unit coordinates to grid, then to SVG (same as terrain)
  const unitToSvg = (x: number, y: number) => {
    // Use same formula as terrain: direct mapping for 50x50 map
    const gridX = Math.floor(x);
    const gridY = Math.floor(y);
    return gridToSvg(gridX, gridY);
  };

  if (!gameState) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
      {error ? (
        <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg">
          <p className="font-bold">Error loading game</p>
          <p className="text-sm">{error}</p>
          <button onClick={fetchGameState} aria-label="再試行" className="mt-2 px-4 py-1 bg-red-600 hover:bg-red-500 rounded text-sm">Retry</button>
        </div>
      ) : (
        <div>Loading...</div>
      )}
    </div>
  );

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
      {/* Header - compact */}
      <header className={`border-b border-gray-700/50 px-4 py-2 flex justify-between items-center shrink-0 backdrop-blur-sm ${gameState.is_night ? 'bg-slate-900/80' : 'bg-gray-800/80'}`}>
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">作戦級CPX</h1>
          <button onClick={() => setShowHelp(!showHelp)} aria-label="ヘルプ表示切替" className="text-xs bg-gray-700/50 hover:bg-gray-600/50 px-3 py-1 rounded backdrop-blur transition-colors">{showHelp ? 'ガイド' : '表示'}</button>
        </div>
        <div className="flex gap-6 text-sm items-center">
          <span className="text-gray-400 font-medium">{gameState.date}</span>
          <span className="text-blue-400 font-bold">T{gameState.turn}</span>
          <span className={`font-bold px-2 py-0.5 rounded ${gameState.is_night ? 'bg-indigo-900/50 text-indigo-300' : 'bg-yellow-900/50 text-yellow-300'}`}>
            {gameState.is_night ? '🌙' : '☀️'} {gameState.time}
          </span>
          <span className="text-green-400 font-medium">{gameState.weather}</span>
          {gameState.weather_effects && (
            <span className="text-xs text-gray-500" title={`偵察:${Math.round(gameState.weather_effects.reconnaissance_modifier * 100)}% 機動力:${Math.round(gameState.weather_effects.movement_modifier * 100)}%`}>
              [偵察{Math.round(gameState.weather_effects.reconnaissance_modifier * 100)}%]
            </span>
          )}
        </div>
      </header>

      {showHelp && (
        <div className="bg-blue-900/30 border-b border-blue-700/50 px-4 py-1.5 text-xs shrink-0 backdrop-blur-sm">
          <span className="font-bold text-blue-300">遊び方: </span>
          <span>クリック→命令→ターン進行 | ズーム: Ctrl+ホイール or ボタン</span>
        </div>
      )}

      {/* Main: 3 columns */}
      <div className="flex-1 flex flex-nowrap overflow-hidden">
        {/* Left: Units - expanded to 240px */}
        <div className="bg-gray-800/90 border-r border-gray-700/50 p-3 flex flex-col shrink-0 overflow-y-auto backdrop-blur-sm" style={{ width: '320px', minWidth: '320px', maxWidth: '320px' }}>
          <h3 className="font-bold text-sm mb-3 text-blue-300 border-b border-gray-700/50 pb-2">■ ユニット</h3>
          <div className="space-y-2">
            {gameState.units.map((unit) => (
              <div key={unit.id} onClick={() => setSelectedUnit(unit)}
                className={`p-3 rounded-lg cursor-pointer text-xs transition-all ${selectedUnit?.id === unit.id ? 'bg-blue-600/80 shadow-lg shadow-blue-900/50' : 'bg-gray-700/50 hover:bg-gray-600/50'} ${unit.side === 'enemy' ? 'opacity-70' : ''}`}>
                <div className="flex justify-between items-center">
                  <span className="font-bold">{unit.name}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: getStatusColor(unit.status) + '30', color: getStatusColor(unit.status) }}>{getStatusLabel(unit.status)}</span>
                </div>
                <div className="text-gray-400 text-[10px] mt-1 flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-gray-800/50">{unit.type}</span>
                  <span className={unit.side === 'player' ? 'text-blue-400' : 'text-red-400'}>{unit.side === 'player' ? '自軍' : '敵軍'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center: Map (clipped) */}
        <div className="flex-1 relative bg-gray-900 overflow-hidden">
          <div
            ref={containerRef}
            className="absolute inset-0 overflow-hidden"
            style={{ clipPath: 'inset(0 0 0 0)' }}
          >
            <svg
              viewBox="0 0 50 50"
              className="w-full h-full"
              style={{
                background: gameState.is_night ? '#0f172a' : '#1e293b',
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: 'center center',
                willChange: 'transform',
                transition: isPanning ? 'none' : 'transform 0.1s ease-out',
                cursor: isPanning ? 'grabbing' : 'grab'
              }}
              onWheel={handleWheel}
              onMouseDown={handlePanStart}
              onMouseMove={handlePan}
              onMouseUp={handlePanEnd}
              onMouseLeave={handlePanEnd}
              onClick={() => setTerrainTooltip(null)}
            >
              {/* Grid - optimized with single path elements */}
              <path d={gridLines.minorPath} stroke="#334155" strokeWidth="0.08" fill="none" />
              <path d={gridLines.majorPath} stroke="#1e293b" strokeWidth="0.15" fill="none" />
              {/* Terrain - use memoized data with click for tooltip */}
              {terrainElements.map((t) => t && (
                <g key={t.key} onClick={(e) => {
                  e.stopPropagation();
                  const terrainKey = t.terrainType || 'plain';
                  const info = gameState?.terrain_info?.[terrainKey];
                  if (info) {
                    setTerrainTooltip({ x: e.clientX, y: e.clientY, terrain: terrainKey, info });
                  }
                }} style={{ cursor: 'pointer' }}>
                  <rect x={t.svgX - 0.4} y={t.svgY - 0.4} width="0.8" height="0.8" fill={t.info.color} opacity="0.5" />
                  <text x={t.svgX} y={t.svgY + 0.3} fontSize="0.8" fill="#fff" textAnchor="middle" opacity="0.9">{t.info.symbol}</text>
                </g>
              ))}
              {/* Units - use memoized UnitMarker component */}
              {unitList.map((unit) => (
                <UnitMarker key={unit.id} unit={unit} selectedUnitId={selectedUnit?.id || null} onSelect={handleUnitSelect} />
              ))}
            </svg>
          </div>

          {/* Map Controls (outside clipped area) - modern glass style */}
          <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
            <button onClick={handleZoomIn} aria-label="マップをzoom in" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">+</button>
            <button onClick={handleZoomOut} aria-label="マップをzoom out" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">−</button>
            <button onClick={handleZoomReset} aria-label="ズームをリセット" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30">Reset</button>
          </div>

          {/* Map Info - modern style */}
          <div className="absolute bottom-3 left-3 bg-gray-900/80 backdrop-blur p-2 rounded-lg text-xs border border-gray-700/50 z-10 flex gap-4">
            <span className="text-blue-400 font-medium">自軍: {gameState.units.filter(u => u.side === 'player').length}</span>
            <span className="text-red-400 font-medium">敵軍: {gameState.units.filter(u => u.side === 'enemy').length}</span>
            <span className="text-gray-400">ズーム: {Math.round(zoom * 100)}%</span>
          </div>

          {/* Terrain Tooltip */}
          {terrainTooltip && (
            <div
              className="fixed z-50 bg-gray-900/95 backdrop-blur p-3 rounded-lg text-xs border border-gray-600/50 shadow-xl"
              style={{
                left: terrainTooltip.x + 15,
                top: terrainTooltip.y + 15,
                pointerEvents: 'none'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg" style={{ color: terrainTooltip.info.color }}>{terrainTooltip.info.symbol}</span>
                <span className="font-bold text-gray-100">{terrainTooltip.info.name}</span>
              </div>
              <div className="text-gray-400 text-[10px]">クリックで情報表示</div>
            </div>
          )}
        </div>

        {/* Right: Orders + Logs - expanded to 320px */}
        <div className="bg-gray-800/90 border-l border-gray-700/50 flex flex-col shrink-0 overflow-hidden backdrop-blur-sm" style={{ width: '400px', minWidth: '400px', maxWidth: '400px' }}>
          {/* Tab system */}
          <div className="flex border-b border-gray-700/50 shrink-0">
            <button className="flex-1 p-2 text-xs font-bold text-blue-300 border-b-2 border-blue-500 bg-blue-900/20">情報</button>
            <button className="flex-1 p-2 text-xs font-bold text-gray-400 hover:text-gray-300">ログ</button>
          </div>

          {selectedUnit ? (
            <div className="p-3 border-b border-gray-700/50 bg-blue-900/20 shrink-0">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-sm text-blue-300">{selectedUnit.name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: getStatusColor(selectedUnit.status) + '30', color: getStatusColor(selectedUnit.status) }}>
                  {getStatusLabel(selectedUnit.status)}
                </span>
              </div>
              {/* Unit Status Details - improved layout */}
              <div className="mb-3 bg-gray-700/30 rounded-lg p-2 text-xs space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">戦力</span>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-gray-600 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${selectedUnit.strength}%`, backgroundColor: getStatusColor(selectedUnit.status) }} />
                    </div>
                    <span className={selectedUnit.strength < 50 ? 'text-red-400' : 'text-green-400'}>{selectedUnit.strength}%</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-center p-1.5 bg-gray-800/50 rounded">
                    <div className="text-gray-500 text-[10px]">弾薬</div>
                    <div className={selectedUnit.ammo === 'exhausted' ? 'text-red-400' : selectedUnit.ammo === 'depleted' ? 'text-yellow-400' : 'text-green-400'}>
                      {selectedUnit.ammo === 'full' ? '充足' : selectedUnit.ammo === 'depleted' ? '低下' : '枯渇'}
                    </div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-800/50 rounded">
                    <div className="text-gray-500 text-[10px]">燃料</div>
                    <div className={selectedUnit.fuel === 'exhausted' ? 'text-red-400' : selectedUnit.fuel === 'depleted' ? 'text-yellow-400' : 'text-green-400'}>
                      {selectedUnit.fuel === 'full' ? '充足' : selectedUnit.fuel === 'depleted' ? '低下' : '枯渇'}
                    </div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-800/50 rounded">
                    <div className="text-gray-500 text-[10px]">整備</div>
                    <div className={selectedUnit.readiness === 'exhausted' ? 'text-red-400' : selectedUnit.readiness === 'depleted' ? 'text-yellow-400' : 'text-green-400'}>
                      {selectedUnit.readiness === 'full' ? '充足' : selectedUnit.readiness === 'depleted' ? '低下' : '枯渇'}
                    </div>
                  </div>
                </div>
                <div className="flex justify-between text-gray-400 pt-1 border-t border-gray-600/30">
                  <span>位置</span>
                  <span className="text-gray-300">X:{selectedUnit.x.toFixed(1)} Y:{selectedUnit.y.toFixed(1)}</span>
                </div>
              </div>
              <textarea value={orderInput} onChange={(e) => setOrderInput(e.target.value)}
                placeholder="命令を入力..." className="w-full bg-gray-700/50 border border-gray-600/50 rounded-lg p-2 text-xs h-16 mb-2 focus:border-blue-500 focus:outline-none backdrop-blur" />
              <div className="flex gap-2">
                <button onClick={parseOrder} disabled={loading || !orderInput.trim()} aria-label="命令を解析" className="flex-1 bg-blue-600/80 hover:bg-blue-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">解析</button>
                {parsedOrder && (
                  <button onClick={submitOrder} disabled={loading} aria-label="命令を決定" className="flex-1 bg-green-600/80 hover:bg-green-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">決定</button>
                )}
              </div>
              {parsedOrder && (
                <div className="mt-2 bg-green-900/30 rounded-lg p-2 text-xs">
                  <span className="text-green-400 font-bold">{parsedOrder.order_type}</span> - {parsedOrder.intent}
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 border-b border-gray-700/50 text-center text-gray-500 text-xs shrink-0 bg-gray-800/30">
              ユニットを選択してください
            </div>
          )}

          {/* Battle Logs */}
          <div className="flex-1 overflow-y-auto p-3">
            <h3 className="font-bold text-sm mb-3 text-blue-300 border-b border-gray-700/50 pb-2">■ 戦闘ログ</h3>
            {turnLogs.length > 0 ? (
              <div className="space-y-3 text-xs">
                {turnLogs.map((log, idx) => (
                  <div key={idx} className="bg-gray-700/30 rounded-lg p-2">
                    <div className="font-bold text-yellow-400 text-[10px] mb-1">T{log.turn}</div>
                    {log.orders.map((order, i) => (
                      <div key={i} className="flex items-center gap-2 py-0.5">
                        <span>{getOutcomeIcon(order.outcome, order.unit)}</span>
                        <span className="text-gray-300 truncate">{order.unit}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-xs">ターン進行で記録されます</p>
            )}
          </div>

          {/* Advance Turn */}
          <div className="p-3 border-t border-gray-700/50 shrink-0 bg-gray-800/50 space-y-2">
            <button onClick={advanceTurn} disabled={loading} aria-label="ターン進行" className="w-full bg-purple-600/80 hover:bg-purple-600 disabled:bg-gray-600/50 rounded-lg p-3 text-sm font-bold transition-all shadow-lg shadow-purple-900/30">
              ▶ ターン進行
            </button>
            <button onClick={endGame} aria-label="ゲームを終了" className="w-full bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 rounded-lg p-2 text-xs font-medium transition-colors">
              End Mission / Debriefing
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Bar - new */}
      <div className="h-12 bg-gray-800/90 border-t border-gray-700/50 flex items-center justify-between px-4 shrink-0 backdrop-blur-sm">
        <div className="flex items-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">ターン</span>
            <span className="font-bold text-blue-400">T{gameState.turn}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">フェーズ</span>
            <span className="font-medium text-cyan-400">{gameState.phase}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">時間</span>
            <span className={gameState.is_night ? 'text-indigo-400' : 'text-yellow-400'}>{gameState.is_night ? '夜' : '昼'} {gameState.time}</span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-blue-400 font-medium">自軍</span>
            <span className="text-green-400">{gameState.units.filter(u => u.side === 'player' && u.status !== 'destroyed').length}部隊</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-red-400 font-medium">敵軍</span>
            <span className="text-gray-400">{gameState.units.filter(u => u.side === 'enemy' && u.status !== 'destroyed').length}部隊</span>
          </div>
          <div className="flex items-center gap-2 px-2 py-1 bg-gray-700/50 rounded">
            <span className="text-gray-400">ズーム</span>
            <span className="font-medium">{Math.round(zoom * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function GamePage() {
  return (
    <Suspense fallback={
      <div className="h-screen bg-gray-900 flex items-center justify-center text-white">
        Loading...
      </div>
    }>
      <GameContent />
    </Suspense>
  );
}
