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

  // NATO APP-6 symbol paths for unit types
  const getNatoSymbol = (unitType: string) => {
    const symbols: Record<string, { path: string; transform: string }> = {
      infantry: { path: 'M25 35 L75 65 M75 35 L25 65', transform: '' },
      armor: { path: 'M35 50 L55 35 L55 45 L80 45 L80 55 L55 55 L55 65 Z M65 50 L45 35 L45 45 L20 45 L20 55 L45 55 L45 65 Z', transform: '' },
      artillery: { path: 'M50 35 L50 65 M30 50 L70 50', transform: '' },
      'combined_arms': { path: 'M30 40 L70 40 L70 60 L30 60 Z', transform: '' },
      reconnaissance: { path: 'M50 35 L70 50 L50 65 L30 50 Z', transform: '' },
      'air_defense': { path: 'M50 38 L60 58 L50 52 L40 58 Z M50 38 L50 28 M35 62 L65 62', transform: '' },
    };
    return symbols[unitType] || symbols.infantry;
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

  // Convert 50x50 coordinates to 10x10 grid display
  // terrain x,y (0-49) -> grid cell (0-9)
  const coordToGrid = (x: number, y: number) => ({
    gridX: Math.floor(x / 5),
    gridY: Math.floor(y / 5)
  });

  // Convert grid cell to SVG display
  const gridToSvg = (gridX: number, gridY: number) => ({
    x: gridX * 5 + 2.5,
    y: gridY * 5 + 2.5
  });

  // Convert unit coordinates to grid, then to SVG (same as terrain)
  // Unit coordinates are in grid scale (0-20), terrain uses 50x50, need same conversion
  const unitToSvg = (x: number, y: number) => {
    // Use same formula as terrain: divide by 5 to get grid cell
    const gridX = Math.floor(x / 5);
    const gridY = Math.floor(y / 5);
    return gridToSvg(gridX, gridY);
  };

  if (!gameState) return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Loading...</div>;

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
      {/* Header - compact */}
      <header className={`border-b border-gray-700/50 px-4 py-2 flex justify-between items-center shrink-0 backdrop-blur-sm ${gameState.is_night ? 'bg-slate-900/80' : 'bg-gray-800/80'}`}>
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">作戦級CPX</h1>
          <button onClick={() => setShowHelp(!showHelp)} className="text-xs bg-gray-700/50 hover:bg-gray-600/50 px-3 py-1 rounded backdrop-blur transition-colors">{showHelp ? 'ガイド' : '表示'}</button>
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
                transform: `scale(${zoom})`,
                transformOrigin: 'center center',
                transition: 'transform 0.1s ease-out'
              }}
              onWheel={handleWheel}
            >
              {/* Grid - fixed subtle grid lines */}
              {[...Array(11)].map((_, i) => (
                <g key={`grid-${i}`}>
                  <line x1={i * 5} y1="0" x2={i * 5} y2="50" stroke="#1e293b" strokeWidth="0.15" />
                  <line x1="0" y1={i * 5} x2="50" y2={i * 5} stroke="#1e293b" strokeWidth="0.15" />
                </g>
              ))}
              {/* Terrain - deduplicate by grid cell */}
              {(() => {
                const terrainByGrid: Record<string, { key: string; terrainType: string }> = {};
                // Group terrain by grid cell (use first non-plain terrain per cell)
                Object.entries(gameState.terrain).forEach(([key, terrainType]) => {
                  const [x, y] = key.split(',').map(Number);
                  const { gridX, gridY } = coordToGrid(x, y);
                  const gridKey = `${gridX},${gridY}`;
                  // Only keep first non-plain terrain for each grid cell
                  if (!terrainByGrid[gridKey] && terrainType !== 'plain') {
                    terrainByGrid[gridKey] = { key, terrainType };
                  }
                });
                return Object.values(terrainByGrid).map(({ key, terrainType }) => {
                  const [x, y] = key.split(',').map(Number);
                  const { gridX, gridY } = coordToGrid(x, y);
                  const { x: svgX, y: svgY } = gridToSvg(gridX, gridY);
                  const info = gameState.terrain_info?.[terrainType];
                  if (!info) return null;
                  return (
                    <g key={`terrain-${key}`}>
                      <rect x={svgX - 2.25} y={svgY - 2.25} width="4.5" height="4.5" fill={info.color} opacity="0.5" />
                      <text x={svgX} y={svgY + 1.5} fontSize="4" fill="#fff" textAnchor="middle" opacity="0.9">{info.symbol}</text>
                    </g>
                  );
                });
              })()}
              {/* Units - NATO symbols */}
              {gameState.units.map((unit) => {
                // Unit coordinates are in grid scale (0-20), convert using same formula as terrain
                const { x: svgX, y: svgY } = unitToSvg(unit.x, unit.y);
                const sideColor = getSideColor(unit.side);
                const symbol = getNatoSymbol(unit.type);
                const isSelected = selectedUnit?.id === unit.id;
                return (
                  <g key={unit.id} onClick={() => setSelectedUnit(unit)} style={{ cursor: 'pointer' }}>
                    {/* Unit frame - NATO style rectangle */}
                    <rect x={svgX - 2.2} y={svgY - 1.8} width="4.4" height="3.6" fill={sideColor} stroke={isSelected ? '#fff' : 'none'} strokeWidth="0.3" opacity="0.95"/>
                    {/* NATO symbol inside - simplified without transform */}
                    <text x={svgX} y={svgY + 0.5} fontSize="3" fill="#fff" textAnchor="middle" fontWeight="bold">
                      {unit.type === 'infantry' ? '✕' : unit.type === 'armor' ? '⇒' : unit.type === 'artillery' ? '+' : unit.type === 'reconnaissance' ? '◇' : unit.type === 'combined_arms' ? '■' : '✕'}
                    </text>
                    {/* Unit name */}
                    <text x={svgX + 3} y={svgY + 3} fontSize="2" fill="#fff" fontWeight="bold">{unit.name}</text>
                    {/* Status indicator */}
                    <rect x={svgX + 1.5} y={svgY + 1.5} width="1" height="0.8" fill={getStatusColor(unit.status)} stroke="#000" strokeWidth="0.1"/>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Map Controls (outside clipped area) - modern glass style */}
          <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
            <button onClick={() => setZoom(z => Math.min(3, z + 0.2))} className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">+</button>
            <button onClick={() => setZoom(z => Math.max(0.5, z - 0.2))} className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">−</button>
            <button onClick={() => setZoom(1)} className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30">Reset</button>
          </div>

          {/* Map Info - modern style */}
          <div className="absolute bottom-3 left-3 bg-gray-900/80 backdrop-blur p-2 rounded-lg text-xs border border-gray-700/50 z-10 flex gap-4">
            <span className="text-blue-400 font-medium">自軍: {gameState.units.filter(u => u.side === 'player').length}</span>
            <span className="text-red-400 font-medium">敵軍: {gameState.units.filter(u => u.side === 'enemy').length}</span>
            <span className="text-gray-400">ズーム: {Math.round(zoom * 100)}%</span>
          </div>
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
                <button onClick={parseOrder} disabled={loading || !orderInput.trim()} className="flex-1 bg-blue-600/80 hover:bg-blue-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">解析</button>
                {parsedOrder && (
                  <button onClick={submitOrder} disabled={loading} className="flex-1 bg-green-600/80 hover:bg-green-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">決定</button>
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
                        <span>{getOutcomeIcon(order.outcome)}</span>
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
          <div className="p-3 border-t border-gray-700/50 shrink-0 bg-gray-800/50">
            <button onClick={advanceTurn} disabled={loading} className="w-full bg-purple-600/80 hover:bg-purple-600 disabled:bg-gray-600/50 rounded-lg p-3 text-sm font-bold transition-all shadow-lg shadow-purple-900/30">
              ▶ ターン進行
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
