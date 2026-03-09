'use client';

import { useState, useEffect, useRef, useMemo, useCallback, memo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import API from '../lib/api';
import type { Unit, GameState, Sitrep, TurnLog } from '@shared/types';

// Memoized Unit component for performance
// FoW display: show exact position marker and UI position marker separately
const UnitMarker = memo(function UnitMarker({
  unit,
  selectedUnitId,
  onSelect,
  showExactPosition = false
}: {
  unit: Unit;
  selectedUnitId: number | null;
  onSelect: (unit: Unit) => void;
  showExactPosition?: boolean; // Show exact position marker (for internal/debug view)
}) {
  // FoW: Determine displayed position based on observation confidence
  const isEnemy = unit.side === 'enemy';
  const confidence = unit.observation_confidence;
  const hasEstimatedPosition = isEnemy && (confidence === 'unknown' || confidence === 'estimated') &&
    unit.estimated_x !== undefined && unit.estimated_y !== undefined;

  // UI display position (what player sees)
  const displayX = hasEstimatedPosition ? unit.estimated_x! : unit.x;
  const displayY = hasEstimatedPosition ? unit.estimated_y! : unit.y;

  // Exact position (true position - for internal use)
  const exactX = unit.x;
  const exactY = unit.y;

  const svgX = Math.floor(displayX) + 0.5;
  const svgY = Math.floor(displayY) + 0.5;
  const exactSvgX = Math.floor(exactX) + 0.5;
  const exactSvgY = Math.floor(exactY) + 0.5;
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

  // Observation confidence styling for enemy units - FoW display
  const confidenceScore = unit.confidence_score;
  let confidenceOpacity = 1.0;
  let confidenceBorder = false;
  let confidenceLabel = '';
  let isEstimatedMarker = false; // Show different marker for estimated position

  if (isEnemy && confidence) {
    if (confidence === 'unknown') {
      confidenceOpacity = 0.5; // Unknown - more transparent
      confidenceBorder = true;
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : '?';
      isEstimatedMarker = hasEstimatedPosition;
    } else if (confidence === 'estimated') {
      confidenceOpacity = 0.75; // Estimated - slightly transparent
      confidenceBorder = true;
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : '~';
      isEstimatedMarker = hasEstimatedPosition;
    } else {
      // confirmed - fully opaque, no border
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : 'OK';
    }
  }

  // FoW marker: different symbol for estimated position
  const markerSymbol = isEstimatedMarker ? '?' : symbol;

  return (
    <g onClick={() => onSelect(unit)} style={{ cursor: 'pointer' }}>
      {/* Exact position marker - shown when showExactPosition is true (for internal/debug view) */}
      {showExactPosition && isEnemy && (
        <g>
          <circle cx={exactSvgX} cy={exactSvgY} r="0.5" fill="none" stroke="#ff00ff" strokeWidth="0.15" strokeDasharray="0.15,0.1" opacity={0.8} />
          <text x={exactSvgX - 0.8} y={exactSvgY - 0.6} fontSize="0.35" fill="#ff00ff" fontWeight="bold" opacity={0.9}>
            EXACT
          </text>
        </g>
      )}
      {/* FoW estimated position marker - dashed circle */}
      {isEstimatedMarker && (
        <circle cx={svgX} cy={svgY} r="0.7" fill="none" stroke="#fbbf24" strokeWidth="0.1" strokeDasharray="0.2,0.1" opacity={confidenceOpacity * 0.7} />
      )}
      <rect x={svgX - 0.6} y={svgY - 0.5} width="1.2" height="1.0"
        fill={sideColor} stroke={isSelected ? '#fff' : (confidenceBorder ? '#fbbf24' : 'none')} strokeWidth="0.1" opacity={confidenceOpacity * 0.95}/>
      <text x={svgX} y={svgY + 0.2} fontSize="0.8" fill="#fff" textAnchor="middle" fontWeight="bold" opacity={confidenceOpacity}>
        {markerSymbol}
      </text>
      <text x={svgX + 0.8} y={svgY + 0.8} fontSize="0.5" fill="#fff" stroke="#000" strokeWidth="0.15" paintOrder="stroke" fontWeight="bold" opacity={confidenceOpacity}>
        {unit.name}{confidenceLabel ? ` (${confidenceLabel})` : ''}
      </text>
      <rect x={svgX + 0.4} y={svgY + 0.4} width="0.3" height="0.2" fill={statusColor} stroke="#000" strokeWidth="0.05" opacity={confidenceOpacity}/>
    </g>
  );
});

// Grid constants - 12x8 fixed grid per Issue #41
const GRID_WIDTH = 12;
const GRID_HEIGHT = 8;

function GameContent() {
  const searchParams = useSearchParams();
  const gameIdParam = searchParams.get('gameId');
  const router = useRouter();
  const [gameId, setGameId] = useState<number | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [sitrep, setSitrep] = useState<Sitrep | null>(null);
  const [sitrepHistory, setSitrepHistory] = useState<Sitrep[]>([]); // SITREP history stack
  const [orderInput, setOrderInput] = useState('');
  const [parsedOrder, setParsedOrder] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null);
  const [showHelp, setShowHelp] = useState(true);
  const [turnLogs, setTurnLogs] = useState<TurnLog[]>([]);
  const [zoom, setZoom] = useState(1);
  const [showExactPosition, setShowExactPosition] = useState(false); // FoW debug: show exact position markers
  const [error, setError] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [battleOdds, setBattleOdds] = useState<{ attacker: string; defender: string; odds: string; details: string } | null>(null);
  const [gameMode, setGameMode] = useState<'classic' | 'arcade'>('classic'); // Game mode: classic (text) or arcade (buttons)
  const [activeTab, setActiveTab] = useState<'info' | 'logs' | 'history'>('info'); // Right sidebar tab
  // Map pan state (for drag to pan)
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [didPan, setDidPan] = useState(false);  // Track if actual panning occurred
  const [terrainTooltip, setTerrainTooltip] = useState<{ x: number; y: number; terrain: string; info: { name: string; symbol: string; color: string } } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Resolve gameId from URL param or API
  useEffect(() => {
    if (gameIdParam) {
      const id = parseInt(gameIdParam, 10);
      if (!isNaN(id) && id > 0) {
        setGameId(id);
        return;
      }
    }
    // No gameId in URL, fetch game list to find the first available game
    fetch(`${API.baseUrl}/api/games/`)
      .then(res => res.json())
      .then(games => {
        if (games && games.length > 0) {
          // Redirect to first available game
          router.replace(`/game?gameId=${games[0].id}`);
        } else {
          // No games available, redirect to new game page
          router.replace('/new-game');
        }
      })
      .catch(() => {
        // Error fetching games, redirect to new game page
        router.replace('/new-game');
      });
  }, [gameIdParam, router]);

  useEffect(() => {
    if (gameId !== null) {
      fetchGameState();
    }
  }, [gameId]);

  const fetchGameState = async () => {
    if (gameId === null) return;
    try {
      const res = await fetch(API.gameState(gameId));
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
    if (!orderInput.trim() || gameId === null) return;
    setLoading(true);
    try {
      const res = await fetch(API.parseOrder, {
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
    if (!parsedOrder || !selectedUnit || gameId === null) return;
    setLoading(true);
    try {
      await fetch(API.orders, {
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

  // Arcade mode: quick command submission
  const submitArcadeCommand = async (command: string) => {
    if (!selectedUnit || gameId === null) return;
    setLoading(true);
    try {
      // Map arcade commands to order types
      const orderTypeMap: Record<string, string> = {
        'move': 'move',
        'attack': 'attack',
        'defend': 'defend',
        'recon': 'recon',
        'supply': 'supply',
        'strike': 'special',
      };
      const orderType = orderTypeMap[command] || 'move';
      await fetch(API.orders, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unit_id: selectedUnit.id,
          order_type: orderType,
          intent: `Arcade command: ${command}`,
        })
      });
      setSelectedUnit(null);
      fetchGameState();
    } catch (e) { console.error('Failed to submit arcade command:', e); }
    setLoading(false);
  };

  const advanceTurn = async () => {
    if (gameId === null) return;
    setLoading(true);
    try {
      const res = await fetch(API.advanceTurn, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId })
      });
      const data = await res.json();
      // Save current sitrep to history before updating
      if (data.sitrep) {
        setSitrepHistory(prev => [data.sitrep, ...prev].slice(0, 5)); // Keep last 5
        setSitrep(data.sitrep);
      }
      setGameState(prev => prev ? { ...prev, turn: data.turn + 1, time: data.next_time } : null);

      // Refresh game state including units after turn advancement
      const stateRes = await fetch(API.gameState(gameId));
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
    if (gameId === null || !confirm('End the game and view debriefing?')) return;
    try {
      await fetch(API.gameEnd(gameId), {
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

  // Memoized grid lines for 12x8 grid per Issue #41
  const gridLines = useMemo(() => {
    // Minor grid lines (every 1 unit)
    let minorPath = '';
    for (let i = 0; i <= GRID_WIDTH; i++) {
      minorPath += `M${i},0 V${GRID_HEIGHT} M0,${i} H${GRID_WIDTH}`;
    }
    // Major grid lines (every 3 units for 12x8)
    let majorPath = '';
    for (let i = 0; i <= GRID_HEIGHT; i += 3) {
      majorPath += `M${i},0 V${GRID_HEIGHT} M0,${i} H${GRID_WIDTH}`;
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

  // Memoized unit select handler with battle odds calculation
  const handleUnitSelect = useCallback((unit: Unit) => {
    // Don't select unit if user was panning (dragging)
    if (didPan) return;
    setSelectedUnit(unit);

    // Calculate battle odds if player unit selected and enemy in range
    if (unit.side === 'player' && gameState?.units) {
      const enemies = gameState.units.filter(u => u.side === 'enemy' && u.status !== 'destroyed');
      let closestEnemy: Unit | null = null;
      let closestDist = Infinity;

      for (const enemy of enemies) {
        const dist = Math.sqrt(Math.pow(unit.x - enemy.x, 2) + Math.pow(unit.y - enemy.y, 2));
        if (dist < closestDist && dist <= 3) {
          closestDist = dist;
          closestEnemy = enemy;
        }
      }

      if (closestEnemy) {
        const playerStrength = unit.strength * (unit.status === 'intact' ? 1.0 : unit.status === 'light_damage' ? 0.75 : 0.5);
        const enemyStrength = closestEnemy.strength * (closestEnemy.status === 'intact' ? 1.0 : closestEnemy.status === 'light_damage' ? 0.75 : 0.5);
        const ratio = playerStrength / enemyStrength;

        let odds: string;
        let details: string;
        if (ratio >= 2) {
          odds = '有利';
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else if (ratio >= 1.2) {
          odds = '稍有利';
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else if (ratio >= 0.8) {
          odds = '五分';
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else if (ratio >= 0.5) {
          odds = '稍不利';
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else {
          odds = '不利';
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        }

        setBattleOdds({
          attacker: unit.name,
          defender: closestEnemy.name,
          odds,
          details: `${closestEnemy.name}まで${closestDist.toFixed(1)}グリッド - ${details}`
        });
      } else {
        setBattleOdds(null);
      }
    } else {
      setBattleOdds(null);
    }
  }, [didPan, gameState?.units]);

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
          <p className="font-bold">ゲーム読み込みエラー</p>
          <p className="text-sm">{error}</p>
          <button onClick={fetchGameState} aria-label="再試行" className="mt-2 px-4 py-1 bg-red-600 hover:bg-red-500 rounded text-sm">再試行</button>
        </div>
      ) : (
        <div>読み込み中...</div>
      )}
    </div>
  );

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
      {/* Header - compact */}
      <header className={`border-b border-gray-700/50 px-4 py-2 flex justify-between items-center shrink-0 backdrop-blur-sm ${gameState.is_night ? 'bg-slate-900/80' : 'bg-gray-800/80'}`}>
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">作戦級CPX</h1>
          <button onClick={() => router.push('/games')} aria-label="ゲーム一覧" className="text-xs bg-gray-700/50 hover:bg-gray-600/50 px-3 py-1 rounded backdrop-blur transition-colors">一覧</button>
          <button onClick={() => setShowHelp(!showHelp)} aria-label="ヘルプ表示切替" className="text-xs bg-gray-700/50 hover:bg-gray-600/50 px-3 py-1 rounded backdrop-blur transition-colors">{showHelp ? 'ガイド' : '表示'}</button>
          <button onClick={() => setGameMode(m => m === 'classic' ? 'arcade' : 'classic')} aria-label="モード切替" className={`text-xs px-3 py-1 rounded backdrop-blur transition-colors font-medium ${gameMode === 'arcade' ? 'bg-purple-600/80 text-white' : 'bg-gray-700/50 hover:bg-gray-600/50'}`}>
            {gameMode === 'classic' ? 'Classic' : 'Arcade'}
          </button>
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
              viewBox={`0 0 ${GRID_WIDTH} ${GRID_HEIGHT}`}
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
                <UnitMarker key={unit.id} unit={unit} selectedUnitId={selectedUnit?.id || null} onSelect={handleUnitSelect} showExactPosition={showExactPosition} />
              ))}
            </svg>
          </div>

          {/* Map Controls (outside clipped area) - modern glass style */}
          <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
            <button onClick={handleZoomIn} aria-label="マップをzoom in" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">+</button>
            <button onClick={handleZoomOut} aria-label="マップをzoom out" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">−</button>
            <button onClick={handleZoomReset} aria-label="ズームをリセット" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30">Reset</button>
            <button onClick={() => setShowExactPosition(!showExactPosition)} aria-label="FoWデバッグ表示切替" className={`w-9 h-9 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30 ${showExactPosition ? 'bg-purple-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="FoW debug: Show exact positions">
              FoW
            </button>
            <button onClick={() => setShowLegend(!showLegend)} aria-label="凡例表示切替" className={`w-9 h-9 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30 ${showLegend ? 'bg-cyan-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="Legend">
              凡例
            </button>
          </div>

          {/* Map Info - modern style */}
          <div className="absolute bottom-3 left-3 bg-gray-900/80 backdrop-blur p-2 rounded-lg text-xs border border-gray-700/50 z-10 flex gap-4">
            <span className="text-blue-400 font-medium">自軍: {gameState.units.filter(u => u.side === 'player').length}</span>
            <span className="text-red-400 font-medium">敵軍: {gameState.units.filter(u => u.side === 'enemy').length}</span>
            <span className="text-gray-400">ズーム: {Math.round(zoom * 100)}%</span>
          </div>

          {/* Legend Panel - Issue #41 */}
          {showLegend && (
            <div className="absolute top-3 left-3 bg-gray-900/95 backdrop-blur p-3 rounded-lg text-xs border border-cyan-700/50 z-20 shadow-xl">
              <div className="font-bold text-cyan-300 mb-2 border-b border-gray-700/50 pb-1">凡例</div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-blue-500"></div>
                  <span className="text-gray-300">自軍</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-500"></div>
                  <span className="text-gray-300">敵軍</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">✕ 歩兵</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">⇒ 装甲</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">+ 砲兵</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">◇ 偵察</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-yellow-500 text-[10px] border border-yellow-500/50 rounded px-0.5">?</span>
                  <span className="text-gray-300">推定位置</span>
                </div>
                <div className="mt-2 pt-1 border-t border-gray-700/50">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <div className="w-2 h-2 rounded-full bg-gray-500"></div>
                  </div>
                  <div className="text-gray-500 text-[10px]">無→壊</div>
                </div>
              </div>
            </div>
          )}

          {/* Battle Odds Display - Issue #41 */}
          {battleOdds && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-gray-900/95 backdrop-blur p-3 rounded-lg text-xs border border-purple-700/50 z-20 shadow-xl">
              <div className="font-bold text-purple-300 mb-1 text-center">戦闘オッドン</div>
              <div className="flex items-center justify-center gap-3">
                <span className="text-blue-400 font-medium">{battleOdds.attacker}</span>
                <span className="text-gray-400">vs</span>
                <span className="text-red-400 font-medium">{battleOdds.defender}</span>
              </div>
              <div className={`text-center font-bold mt-1 ${
                battleOdds.odds === '有利' ? 'text-green-400' :
                battleOdds.odds === '稍有利' ? 'text-lime-400' :
                battleOdds.odds === '五分' ? 'text-yellow-400' :
                battleOdds.odds === '稍不利' ? 'text-orange-400' :
                'text-red-400'
              }`}>
                {battleOdds.odds}
              </div>
              <div className="text-gray-500 text-[10px] text-center mt-1">{battleOdds.details}</div>
            </div>
          )}

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
            <button onClick={() => setActiveTab('info')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'info' ? 'text-blue-300 border-blue-500 bg-blue-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>情報</button>
            <button onClick={() => setActiveTab('history')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'history' ? 'text-blue-300 border-blue-500 bg-blue-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>履歴</button>
            <button onClick={() => setActiveTab('logs')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'logs' ? 'text-blue-300 border-blue-500 bg-blue-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>ログ</button>
          </div>

          {/* SITREP Card - shown on info tab */}
          {activeTab === 'info' && sitrep && (
            <div className="p-3 border-b border-gray-700/50 bg-gradient-to-r from-blue-900/30 to-purple-900/30 shrink-0">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-sm text-cyan-300">■ SITREP T{sitrep.turn}</span>
                <span className="text-[10px] text-gray-400">{new Date(sitrep.timestamp).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              {/* Display sections by type */}
              <div className="space-y-2 text-xs">
                {sitrep.sections?.map((section, idx) => (
                  <div key={idx} className="bg-gray-800/50 rounded p-2">
                    <div className="text-gray-400 text-[10px] mb-1">
                      {section.type === 'overview' && '戦況'}
                      {section.type === 'unit_status' && '損害'}
                      {section.type === 'enemy_activity' && '敵行動'}
                      {section.type === 'logistics' && '補給'}
                      {section.type === 'orders_result' && '命令結果'}
                      {section.type === 'friction' && '摩擦'}
                      {section.type === 'command' && '命令'}
                    </div>
                    <div className="text-gray-200 line-clamp-2">{section.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SITREP History - previous sitreps */}
          {activeTab === 'info' && sitrepHistory.length > 0 && (
            <div className="p-2 border-b border-gray-700/50 bg-gray-800/30 shrink-0">
              <div className="text-[10px] text-gray-500 mb-1">履歴</div>
              <div className="flex gap-1 overflow-x-auto">
                {sitrepHistory.map((hist, idx) => (
                  <button key={idx} onClick={() => setSitrep(hist)}
                    className="text-[10px] px-2 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded text-gray-400 shrink-0">
                    T{hist.turn}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* SITREP History Stack - shown on history tab */}
          {activeTab === 'history' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              <h3 className="font-bold text-sm mb-3 text-cyan-300 border-b border-gray-700/50 pb-2">■ SITREP履歴スタック</h3>
              {sitrepHistory.length > 0 ? (
                <div className="space-y-3">
                  {sitrepHistory.map((histSitrep, idx) => (
                    <div
                      key={histSitrep.turn}
                      onClick={() => setSitrep(histSitrep)}
                      className={`p-3 rounded-lg cursor-pointer transition-all border ${
                        idx === 0
                          ? 'bg-purple-900/40 border-purple-500/50'
                          : 'bg-gray-800/40 border-gray-700/30 hover:border-gray-600/50'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-sm text-cyan-300">■ SITREP T{histSitrep.turn}</span>
                        {idx === 0 && <span className="text-[10px] px-1.5 py-0.5 bg-purple-600/50 rounded text-purple-200">最新</span>}
                      </div>
                      {/* Quick summary - access sections as array */}
                      <div className="text-xs text-gray-400 space-y-1">
                        {histSitrep.sections?.filter(s => s.type === 'overview').slice(0, 1).map((section, i) => (
                          <div key={i} className="line-clamp-2">{section.content}</div>
                        ))}
                        {histSitrep.sections && histSitrep.sections.length > 0 && (
                          <div className="text-yellow-400 text-[10px]">
                            {histSitrep.sections.length}セクション
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-xs">ターン進行で履歴が追加されます</p>
              )}
            </div>
          )}

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
              {gameMode === 'arcade' ? (
                // Arcade mode: 6 command buttons
                <div className="space-y-2">
                  <div className="text-xs text-purple-300 font-medium mb-1">コマンドを選択:</div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {[
                      { cmd: 'move', label: '移動', icon: '>', color: 'bg-blue-600' },
                      { cmd: 'attack', label: '攻撃', icon: 'X', color: 'bg-red-600' },
                      { cmd: 'defend', label: '防御', icon: 'O', color: 'bg-green-600' },
                      { cmd: 'recon', label: '偵察', icon: '?', color: 'bg-cyan-600' },
                      { cmd: 'supply', label: '補給', icon: '+', color: 'bg-yellow-600' },
                      { cmd: 'strike', label: '特攻', icon: '*', color: 'bg-purple-600' },
                    ].map((btn) => (
                      <button key={btn.cmd} onClick={() => submitArcadeCommand(btn.cmd)} disabled={loading}
                        className={`${btn.color} hover:opacity-90 disabled:opacity-50 rounded-lg p-2 text-xs font-bold transition-all flex flex-col items-center gap-0.5`}>
                        <span className="text-sm">{btn.icon}</span>
                        <span>{btn.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                // Classic mode: text input
                <>
                  <textarea value={orderInput} onChange={(e) => setOrderInput(e.target.value)}
                    placeholder="命令を入力..." className="w-full bg-gray-700/50 border border-gray-600/50 rounded-lg p-2 text-xs h-16 mb-2 focus:border-blue-500 focus:outline-none backdrop-blur" />
                  <div className="flex gap-2">
                    <button onClick={parseOrder} disabled={loading || !orderInput.trim()} aria-label="命令を解析" className="flex-1 bg-blue-600/80 hover:bg-blue-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">解析</button>
                    {parsedOrder && (
                      <button onClick={submitOrder} disabled={loading} aria-label="命令を決定" className="flex-1 bg-green-600/80 hover:bg-green-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">決定</button>
                    )}
                  </div>
                </>
              )}
              {parsedOrder && gameMode === 'classic' && (
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

          {/* Battle Logs - show on both tabs but different amount */}
          <div className="flex-1 overflow-y-auto p-3">
            <h3 className="font-bold text-sm mb-3 text-blue-300 border-b border-gray-700/50 pb-2">■ 戦闘ログ {activeTab === 'info' ? '(最新3件)' : '(全履歴)'}</h3>
            {turnLogs.length > 0 ? (
              <div className="space-y-3 text-xs">
                {(activeTab === 'info' ? turnLogs.slice(-3) : turnLogs).map((log, idx) => (
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
        読み込み中...
      </div>
    }>
      <GameContent />
    </Suspense>
  );
}
