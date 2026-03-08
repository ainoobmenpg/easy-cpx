'use client';

import { useState, useEffect, useRef } from 'react';

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

export default function GamePage() {
  const [gameId] = useState(1);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [sitrep, setSitrep] = useState<Sitrep | null>(null);
  const [orderInput, setOrderInput] = useState('');
  const [parsedOrder, setParsedOrder] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null);
  const [showHelp, setShowHelp] = useState(true);
  const [turnLogs, setTurnLogs] = useState<TurnLog[]>([]);
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchGameState(); }, [gameId]);

  const fetchGameState = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/game/${gameId}/state`);
      const data = await res.json();
      setGameState(data);
    } catch (e) { console.error('Failed to fetch game state:', e); }
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
      const newLog: TurnLog = {
        turn: data.turn,
        orders: (data.results || []).map((r: any) => ({
          unit: r.unit_name || `Unit ${r.order_id}`,
          outcome: r.outcome
        })),
      };
      setTurnLogs(prev => [newLog, ...prev]);
    } catch (e) { console.error('Failed to advance turn:', e); }
    setLoading(false);
  };

  // Zoom with Ctrl+Wheel only
  const handleWheel = (e: React.WheelEvent) => {
    if (!e.ctrlKey) return; // Let normal scroll pass through
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.2 : 0.2;
    setZoom(z => Math.max(0.5, Math.min(3, z + delta)));
  };

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
  const getOutcomeIcon = (outcome: string) => {
    const icons: Record<string, string> = { success: '✅', partial: '⚠️', failed: '❌', blocked: '🚫', cancelled: '⏸️' };
    return icons[outcome] || '❓';
  };

  if (!gameState) return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Loading...</div>;

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
      {/* Header */}
      <header className={`border-b border-gray-700 p-2 flex justify-between items-center shrink-0 ${gameState.is_night ? 'bg-slate-900' : 'bg-gray-800'}`}>
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-blue-400">作戦級CPX</h1>
          <button onClick={() => setShowHelp(!showHelp)} className="text-xs bg-gray-700 px-2 py-1 rounded">{showHelp ? 'ガイド' : '表示'}</button>
        </div>
        <div className="flex gap-4 text-sm items-center">
          <span className="text-gray-400">{gameState.date}</span>
          <span className="text-blue-300">T{gameState.turn}</span>
          <span className={`font-bold ${gameState.is_night ? 'text-indigo-400' : 'text-yellow-300'}`}>
            {gameState.is_night ? '🌙' : '☀️'} {gameState.time}
          </span>
          <span className="text-green-300">{gameState.weather}</span>
          {gameState.weather_effects && (
            <span className="text-xs text-gray-500" title={`偵察:${Math.round(gameState.weather_effects.reconnaissance_modifier * 100)}% 機動力:${Math.round(gameState.weather_effects.movement_modifier * 100)}%`}>
              [偵察{Math.round(gameState.weather_effects.reconnaissance_modifier * 100)}%]
            </span>
          )}
        </div>
      </header>

      {showHelp && (
        <div className="bg-blue-900/50 border-b border-blue-700 p-1 text-xs shrink-0">
          <span className="font-bold text-blue-300">遊び方: </span>
          <span>クリック→命令→ターン進行 | ズーム: Ctrl+ホイール or ボタン</span>
        </div>
      )}

      {/* Main: 3 columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Units */}
        <div className="w-44 bg-gray-800 border-r border-gray-700 p-2 flex flex-col shrink-0 overflow-y-auto">
          <h3 className="font-bold text-sm mb-2 text-blue-300">■ ユニット</h3>
          <div className="space-y-1">
            {gameState.units.map((unit) => (
              <div key={unit.id} onClick={() => setSelectedUnit(unit)}
                className={`p-2 rounded cursor-pointer text-xs ${selectedUnit?.id === unit.id ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'} ${unit.side === 'enemy' ? 'opacity-70' : ''}`}>
                <div className="flex justify-between items-center">
                  <span className="font-bold">{unit.name}</span>
                  <span className="text-[10px]" style={{ color: getStatusColor(unit.status) }}>{getStatusLabel(unit.status)}</span>
                </div>
                <div className="text-gray-400 text-[10px]">{unit.type}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Center: Map (clipped) */}
        <div className="flex-1 relative bg-gray-800 overflow-hidden">
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
                transform: `scale(${zoom})`,
                transformOrigin: 'center center',
                transition: 'transform 0.1s ease-out'
              }}
              onWheel={handleWheel}
            >
              {/* Grid */}
              {[...Array(11)].map((_, i) => (
                <g key={`grid-${i}`}>
                  <line x1={i * 5} y1="0" x2={i * 5} y2="50" stroke="#334155" strokeWidth="0.1" />
                  <line x1="0" y1={i * 5} x2="50" y2={i * 5} stroke="#334155" strokeWidth="0.1" />
                </g>
              ))}
              {/* Terrain */}
              {gameState.terrain && Object.entries(gameState.terrain).map(([key, terrainType]) => {
                const [x, y] = key.split(',').map(Number);
                const info = gameState.terrain_info?.[terrainType];
                if (!info || terrainType === 'plain') return null;
                return (
                  <g key={`terrain-${key}`}>
                    <rect x={x - 0.45} y={y - 0.45} width="0.9" height="0.9" fill={info.color} opacity="0.4" />
                    <text x={x} y={y + 0.3} fontSize="0.8" fill="#fff" textAnchor="middle" opacity="0.7">{info.symbol}</text>
                  </g>
                );
              })}
              {/* Units */}
              {gameState.units.map((unit) => (
                <g key={unit.id} onClick={() => setSelectedUnit(unit)} style={{ cursor: 'pointer' }}>
                  <circle cx={unit.x} cy={unit.y} r="2.5" fill={getSideColor(unit.side)} stroke={selectedUnit?.id === unit.id ? '#fff' : 'none'} strokeWidth="0.3" />
                  <text x={unit.x + 3} y={unit.y + 0.8} fontSize="3" fill="#fff" fontWeight="bold">{unit.name}</text>
                  <circle cx={unit.x + 2} cy={unit.y + 2} r="0.8" fill={getStatusColor(unit.status)} stroke="#000" strokeWidth="0.1"/>
                </g>
              ))}
            </svg>
          </div>

          {/* Map Controls (outside clipped area) */}
          <div className="absolute top-2 right-2 flex flex-col gap-1 z-10">
            <button onClick={() => setZoom(z => Math.min(3, z + 0.2))} className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded text-lg font-bold">+</button>
            <button onClick={() => setZoom(z => Math.max(0.5, z - 0.2))} className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded text-lg font-bold">−</button>
            <button onClick={() => setZoom(1)} className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded text-xs">Reset</button>
          </div>

          {/* Map Info */}
          <div className="absolute bottom-2 left-2 bg-gray-900/90 p-1 rounded text-xs border border-gray-600 z-10">
            <span className="text-blue-300">自:{gameState.units.filter(u => u.side === 'player').length}</span>
            <span className="text-red-300 ml-2">敵:{gameState.units.filter(u => u.side === 'enemy').length}</span>
            <span className="text-gray-400 ml-2">{Math.round(zoom * 100)}%</span>
          </div>
        </div>

        {/* Right: Orders + Logs */}
        <div className="w-64 bg-gray-800 border-l border-gray-700 flex flex-col shrink-0 overflow-hidden">
          {selectedUnit ? (
            <div className="p-2 border-b border-gray-700 bg-blue-900/30 shrink-0">
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-sm text-blue-300">{selectedUnit.name}</span>
                <span className="text-[10px] px-1 rounded" style={{ backgroundColor: getStatusColor(selectedUnit.status) + '40', color: getStatusColor(selectedUnit.status) }}>
                  {getStatusLabel(selectedUnit.status)}
                </span>
              </div>
              {/* Unit Status Details */}
              <div className="mb-2 bg-gray-700/50 rounded p-1 text-[10px] space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-400">戦力:</span>
                  <span className={selectedUnit.strength < 50 ? 'text-red-400' : 'text-green-400'}>{selectedUnit.strength}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">弾薬:</span>
                  <span className={selectedUnit.ammo === 'exhausted' ? 'text-red-400' : selectedUnit.ammo === 'depleted' ? 'text-yellow-400' : 'text-green-400'}>
                    {selectedUnit.ammo === 'full' ? '充足' : selectedUnit.ammo === 'depleted' ? '低下' : '枯渇'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">燃料:</span>
                  <span className={selectedUnit.fuel === 'exhausted' ? 'text-red-400' : selectedUnit.fuel === 'depleted' ? 'text-yellow-400' : 'text-green-400'}>
                    {selectedUnit.fuel === 'full' ? '充足' : selectedUnit.fuel === 'depleted' ? '低下' : '枯渇'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">整備:</span>
                  <span className={selectedUnit.readiness === 'exhausted' ? 'text-red-400' : selectedUnit.readiness === 'depleted' ? 'text-yellow-400' : 'text-green-400'}>
                    {selectedUnit.readiness === 'full' ? '充足' : selectedUnit.readiness === 'depleted' ? '低下' : '枯渇'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">位置:</span>
                  <span className="text-gray-300">X:{selectedUnit.x.toFixed(1)} Y:{selectedUnit.y.toFixed(1)}</span>
                </div>
              </div>
              <textarea value={orderInput} onChange={(e) => setOrderInput(e.target.value)}
                placeholder="命令を入力..." className="w-full bg-gray-700 border border-gray-600 rounded p-1 text-xs h-12 mb-1 focus:border-blue-500 focus:outline-none" />
              <div className="flex gap-1">
                <button onClick={parseOrder} disabled={loading || !orderInput.trim()} className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded p-1 text-xs">解析</button>
                {parsedOrder && (
                  <button onClick={submitOrder} disabled={loading} className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded p-1 text-xs">決定</button>
                )}
              </div>
              {parsedOrder && (
                <div className="mt-1 bg-green-900/30 rounded p-1 text-[10px]">
                  <span className="text-green-400 font-bold">{parsedOrder.order_type}</span> - {parsedOrder.intent}
                </div>
              )}
            </div>
          ) : (
            <div className="p-2 border-b border-gray-700 text-center text-gray-500 text-xs shrink-0">
              ユニットを選択
            </div>
          )}

          {/* Battle Logs */}
          <div className="flex-1 overflow-y-auto p-2">
            <h3 className="font-bold text-sm mb-2 text-blue-300">■ 戦闘ログ</h3>
            {turnLogs.length > 0 ? (
              <div className="space-y-2 text-xs">
                {turnLogs.map((log, idx) => (
                  <div key={idx} className="bg-gray-700/50 rounded p-1">
                    <div className="font-bold text-yellow-400 text-[10px]">T{log.turn}</div>
                    {log.orders.map((order, i) => (
                      <div key={i} className="flex items-center gap-1">
                        <span>{getOutcomeIcon(order.outcome)}</span>
                        <span className="text-gray-300 truncate">{order.unit}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-xs">ターン進行で記録</p>
            )}
          </div>

          {/* Advance Turn */}
          <div className="p-2 border-t border-gray-700 shrink-0">
            <button onClick={advanceTurn} disabled={loading} className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded p-2 text-sm font-bold">
              ▶ ターン進行
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
