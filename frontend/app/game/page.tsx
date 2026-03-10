'use client';

import { useState, useEffect, useRef, useMemo, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import API from '../lib/api';
import ReportPanel from '../lib/report-panel';
import ChatPanel from '../lib/chat-panel';
import { useI18n } from '../lib/i18n';
import { useToast } from '../hooks/useToast';
import ErrorDisplay, { LoadingDisplay } from '../components/ErrorDisplay';
import { UnitMarker, getPhaseLinePath, getBoundaryPath, getAirspacePath, getControlMeasureDashArray, CONTROL_MEASURE_COLORS } from '../lib/app6';
import type { Unit, GameState, Sitrep, TurnLog, PhaseLine as PhaseLineType, Boundary as BoundaryType, Airspace as AirspaceType } from '@shared/types';

// Control measures layer visibility state
interface LayerVisibility {
  phaseLines: boolean;
  boundaries: boolean;
  airspaces: boolean;
}

// Grid constants - 12x8 fixed grid per Issue #41
const GRID_WIDTH = 12;
const GRID_HEIGHT = 8;

function GameContent() {
  const { t } = useI18n();
  const { showToast } = useToast();
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
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    phaseLines: true,
    boundaries: true,
    airspaces: true
  });
  const [error, setError] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [battleOdds, setBattleOdds] = useState<{ attacker: string; defender: string; odds: string; details: string } | null>(null);
  const [gameMode, setGameMode] = useState<'classic' | 'arcade'>('classic'); // Game mode: classic (text) or arcade (buttons)
  const [activeTab, setActiveTab] = useState<'plan' | 'sync' | 'situation' | 'sustain' | 'chat'>('situation'); // Right sidebar tab
  // OPORD state for SMESC editor
  const [opordData, setOpordData] = useState<any>(null);
  const [opordLoading, setOpordLoading] = useState(false);
  const [opordEditMode, setOpordEditMode] = useState(false);
  // Map pan state (for drag to pan)
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [didPan, setDidPan] = useState(false);  // Track if actual panning occurred
  const [terrainTooltip, setTerrainTooltip] = useState<{ x: number; y: number; terrain: string; info: { name: string; symbol: string; color: string } } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // Issue #52: Reachable positions for movement preview
  const [reachablePositions, setReachablePositions] = useState<{x: number; y: number; can_reach: boolean}[]>([]);
  // Issue #56: Batch orders for batch submission
  const [pendingOrders, setPendingOrders] = useState<{unit_id: number; order_type: string; intent?: string; location_x?: number; location_y?: number; target_units?: number[]}[]>([]);

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
          router.replace('/games');
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

  // Issue #115: Keyboard shortcuts for accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      // Ignore if Ctrl/Cmd key is pressed (browser shortcuts)
      if (e.ctrlKey || e.metaKey) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'z':
          // Z: Zoom reset
          setZoom(1);
          setPan({ x: 0, y: 0 });
          break;
        case 'l':
          // L: Toggle legend
          setShowLegend(prev => !prev);
          break;
        case 'h':
          // H: Toggle help
          setShowHelp(prev => !prev);
          break;
        case 'm':
          // M: Toggle mode (classic/arcade)
          setGameMode(prev => prev === 'classic' ? 'arcade' : 'classic');
          break;
        case 'p':
          // P: Toggle phase lines
          setLayerVisibility(v => ({ ...v, phaseLines: !v.phaseLines }));
          break;
        case 'b':
          // B: Toggle boundaries
          setLayerVisibility(v => ({ ...v, boundaries: !v.boundaries }));
          break;
        case 'a':
          // A: Toggle airspace
          setLayerVisibility(v => ({ ...v, airspaces: !v.airspaces }));
          break;
        case '=':
        case '+':
          // +: Zoom in
          setZoom(z => Math.min(3, z + 0.2));
          break;
        case '-':
          // -: Zoom out
          setZoom(z => Math.max(0.5, z - 0.2));
          break;
        case 'arrowup':
          // Arrow up: Pan up
          setPan(p => ({ ...p, y: p.y + 50 }));
          break;
        case 'arrowdown':
          // Arrow down: Pan down
          setPan(p => ({ ...p, y: p.y - 50 }));
          break;
        case 'arrowleft':
          // Arrow left: Pan left
          setPan(p => ({ ...p, x: p.x + 50 }));
          break;
        case 'arrowright':
          // Arrow right: Pan right
          setPan(p => ({ ...p, x: p.x - 50 }));
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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
      showToast(`Failed to load game: ${msg}`, 'error');
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
      showToast(`Order submitted: ${parsedOrder.order_type}`, 'success');
    } catch (e) {
      console.error('Failed to submit order:', e);
      showToast('Failed to submit order', 'error');
    }
    setLoading(false);
  };

  // CPX-1: Fetch OPORD data
  const fetchOpord = async () => {
    if (gameId === null) return;
    setOpordLoading(true);
    try {
      const res = await fetch(API.opord(gameId));
      const data = await res.json();
      if (data.success && data.opord) {
        setOpordData(data.opord);
      }
    } catch (e) {
      console.error('Failed to fetch OPORD:', e);
    }
    setOpordLoading(false);
  };

  // CPX-1: Update OPORD data
  const updateOpord = async (updates: any) => {
    if (gameId === null) return;
    setOpordLoading(true);
    try {
      const res = await fetch(API.opord(gameId), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success && data.opord) {
        setOpordData(data.opord);
      }
    } catch (e) {
      console.error('Failed to update OPORD:', e);
    }
    setOpordLoading(false);
    setOpordEditMode(false);
  };

  // Issue #56: Add order to pending batch
  const addToBatch = (command: string, targetUnitId?: number) => {
    if (!selectedUnit) return;
    const orderTypeMap: Record<string, string> = {
      'move': 'move',
      'attack': 'attack',
      'defend': 'defend',
      'recon': 'recon',
      'supply': 'supply',
      'strike': 'special',
    };
    const orderType = orderTypeMap[command] || 'move';

    // Check if this unit already has a pending order
    const existingIndex = pendingOrders.findIndex(o => o.unit_id === selectedUnit.id);
    const newOrder = {
      unit_id: selectedUnit.id,
      order_type: orderType,
      intent: `Arcade: ${command}`,
      location_x: targetUnitId ? undefined : (command === 'move' ? selectedUnit.x + 1 : undefined),
      location_y: targetUnitId ? undefined : (command === 'move' ? selectedUnit.y : undefined),
      target_units: targetUnitId ? [targetUnitId] : undefined,
    };

    if (existingIndex >= 0) {
      // Replace existing order for this unit
      const updated = [...pendingOrders];
      updated[existingIndex] = newOrder;
      setPendingOrders(updated);
    } else {
      setPendingOrders([...pendingOrders, newOrder]);
    }
  };

  // Issue #56: Submit all pending orders as batch
  const submitBatchOrders = async () => {
    if (pendingOrders.length === 0 || gameId === null) return;
    setLoading(true);
    try {
      const res = await fetch(API.turnCommit, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId,
          orders: pendingOrders.map(o => ({
            unit_id: o.unit_id,
            order_type: o.order_type,
            intent: o.intent,
            location_x: o.location_x,
            location_y: o.location_y,
            target_units: o.target_units,
          }))
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPendingOrders([]);
      setSelectedUnit(null);
      setReachablePositions([]);
      // Update game state with results
      if (data.results?.units) {
        setGameState(prev => prev ? { ...prev, units: data.results.units } : null);
      }
      // Add turn log
      setTurnLogs(prev => [{
        turn: data.turn || gameState?.turn || 1,
        orders: [{
          unit: `${pendingOrders.length} units`,
          outcome: 'submitted'
        }]
      }, ...prev]);
    } catch (e) { console.error('Failed to submit batch orders:', e); }
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

  // Performance optimization: rAF for smooth pan/zoom (Issue #116)
  const rafRef = useRef<number | null>(null);
  const pendingPanRef = useRef<{ x: number; y: number } | null>(null);

  // Flush pending pan update via rAF
  const flushPanUpdate = useCallback(() => {
    if (pendingPanRef.current) {
      setPan(pendingPanRef.current);
      pendingPanRef.current = null;
    }
    rafRef.current = null;
  }, []);

  // Zoom with wheel - throttled with rAF
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.2 : 0.2;
    setZoom(z => Math.max(0.5, Math.min(3, z + delta)));
  }, []);

  // Pan handlers - optimized with rAF for 60fps target
  const handlePanStart = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsPanning(true);
    setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    setDidPan(false);
  }, [pan.x, pan.y]);

  const handlePan = useCallback((e: React.MouseEvent) => {
    if (!isPanning) return;
    e.preventDefault();
    setDidPan(true);
    const newPan = { x: e.clientX - panStart.x, y: e.clientY - panStart.y };

    // Use rAF to batch updates for smooth 60fps
    if (rafRef.current === null) {
      rafRef.current = requestAnimationFrame(flushPanUpdate);
    }
    pendingPanRef.current = newPan;
  }, [isPanning, panStart.x, panStart.y, flushPanUpdate]);

  const handlePanEnd = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (pendingPanRef.current) {
      setPan(pendingPanRef.current);
      pendingPanRef.current = null;
    }
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

  // Memoized unit select handler with battle odds calculation and reachable positions
  const handleUnitSelect = useCallback((unit: Unit) => {
    // Don't select unit if user was panning (dragging)
    if (didPan) return;
    setSelectedUnit(unit);

    // Fetch reachable positions for movement preview (Arcade mode)
    if (unit.side === 'player' && gameMode === 'arcade' && gameId !== null) {
      fetch(API.unitReachable(unit.id))
        .then(res => res.json())
        .then(data => {
          if (data.reachable) {
            setReachablePositions(data.reachable.map((r: {x: number, y: number, can_reach: boolean}) => ({
              x: r.x, y: r.y, can_reach: r.can_reach
            })));
          }
        })
        .catch(err => console.error('Failed to fetch reachable positions:', err));
    } else {
      setReachablePositions([]);
    }

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
          odds = t('battleOdds.advantageous');
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else if (ratio >= 1.2) {
          odds = t('battleOdds.slightlyAdvantageous');
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else if (ratio >= 0.8) {
          odds = t('battleOdds.even');
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else if (ratio >= 0.5) {
          odds = t('battleOdds.slightlyDisadvantageous');
          details = `${Math.round(playerStrength)} vs ${Math.round(enemyStrength)}`;
        } else {
          odds = t('battleOdds.disadvantageous');
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
  }, [didPan, gameState?.units, gameMode, gameId]);

  // Memoized unit list for rendering
  const unitList = useMemo(() => gameState?.units || [], [gameState?.units]);

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { intact: '#22c55e', light_damage: '#eab308', medium_damage: '#f97316', heavy_damage: '#ef4444', destroyed: '#6b7280' };
    return colors[status] || '#22c55e';
  };
  const getSideColor = (side: string) => side === 'player' ? '#3b82f6' : '#ef4444';
  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      intact: t('status.intact'),
      light_damage: t('status.lightDamage'),
      medium_damage: t('status.moderateDamage'),
      heavy_damage: t('status.heavyDamage'),
      destroyed: t('status.destroyed')
    };
    return labels[status] || status;
  };
  const getSupplyLabel = (level: string) => {
    const labels: Record<string, string> = {
      full: t('status.full'),
      depleted: t('status.depleted'),
      exhausted: t('status.exhausted')
    };
    return labels[level] || level;
  };
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
        <ErrorDisplay message={error} title={t('game.loadError')} onRetry={fetchGameState} />
      ) : (
        <LoadingDisplay message={t('game.loading')} />
      )}
    </div>
  );

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
      {/* Header - compact */}
      <header className={`border-b border-gray-700/50 px-4 py-2 flex justify-between items-center shrink-0 backdrop-blur-sm ${gameState.is_night ? 'bg-slate-900/80' : 'bg-gray-800/80'}`}>
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">{t('common.gameTitle')}</h1>
          <button onClick={() => router.push('/games')} aria-label={t('game.gameList')} className="text-xs bg-gray-700/50 hover:bg-gray-600/50 px-3 py-1 rounded backdrop-blur transition-colors">{t('game.backToList')}</button>
          <button onClick={() => setShowHelp(!showHelp)} aria-label={t('game.helpToggle')} aria-pressed={showHelp} className="text-xs bg-gray-700/50 hover:bg-gray-600/50 px-3 py-1 rounded backdrop-blur transition-colors">{showHelp ? t('common.guide') : t('common.display')}</button>
          <button onClick={() => setGameMode(m => m === 'classic' ? 'arcade' : 'classic')} aria-label={t('game.modeToggle')} aria-pressed={gameMode === 'arcade'} className={`text-xs px-3 py-1 rounded backdrop-blur transition-colors font-medium ${gameMode === 'arcade' ? 'bg-purple-600/80 text-white' : 'bg-gray-700/50 hover:bg-gray-600/50'}`}>
            {gameMode === 'classic' ? t('gameMode.classic') : t('gameMode.arcade')}
          </button>
        </div>
        <div className="flex gap-6 text-sm items-center">
          <span className="text-gray-400 font-medium">{gameState.date}</span>
          <span className="text-blue-400 font-bold">T{gameState.turn}</span>
          {/* Scoreboard for Arcade mode */}
          {gameState.score && (
            <div className="flex items-center gap-2 px-2 py-0.5 rounded bg-purple-900/30 border border-purple-700/50">
              <span className="text-blue-400 font-bold">{gameState.score.player}</span>
              <span className="text-gray-500">-</span>
              <span className="text-red-400 font-bold">{gameState.score.enemy}</span>
              <span className="text-[10px] text-purple-400">VP</span>
            </div>
          )}
          <span className={`font-bold px-2 py-0.5 rounded ${gameState.is_night ? 'bg-indigo-900/50 text-indigo-300' : 'bg-yellow-900/50 text-yellow-300'}`}>
            {gameState.is_night ? '🌙' : '☀️'} {gameState.time}
          </span>
          <span className="text-green-400 font-medium">{gameState.weather}</span>
          {gameState.weather_effects && (
            <span className="text-xs text-gray-500" title={`偵察:${Math.round(gameState.weather_effects.reconnaissance_modifier * 100)}% 機動力:${Math.round(gameState.weather_effects.movement_modifier * 100)}%`}>
              [偵察{Math.round(gameState.weather_effects.reconnaissance_modifier * 100)}%]
            </span>
          )}
          {/* CPX-CYCLES: Cycle status display */}
          {gameState.cycles && (
            <div className="flex items-center gap-2 text-xs" title="Planning/Air/Logistics Cycles">
              {(gameState.cycles.planning || gameState.cycles.air_tasking || gameState.cycles.logistics) && (
                <>
                  <span className={`px-1.5 py-0.5 rounded ${gameState.cycles.planning?.status === 'on_track' ? 'bg-green-900/50 text-green-400' : gameState.cycles.planning?.status === 'delayed' ? 'bg-yellow-900/50 text-yellow-400' : 'bg-red-900/50 text-red-400'}`}>
                    P:{gameState.cycles.planning?.phase?.[0] || '-'}{gameState.cycles.planning?.deadline_turn || '-'}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded ${gameState.cycles.air_tasking?.status === 'on_track' ? 'bg-green-900/50 text-green-400' : gameState.cycles.air_tasking?.status === 'delayed' ? 'bg-yellow-900/50 text-yellow-400' : 'bg-red-900/50 text-red-400'}`}>
                    A:{gameState.cycles.air_tasking?.phase?.[0] || '-'}{gameState.cycles.air_tasking?.deadline_turn || '-'}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded ${gameState.cycles.logistics?.status === 'on_track' ? 'bg-green-900/50 text-green-400' : gameState.cycles.logistics?.status === 'delayed' ? 'bg-yellow-900/50 text-yellow-400' : 'bg-red-900/50 text-red-400'}`}>
                    L:{gameState.cycles.logistics?.phase?.[0] || '-'}{gameState.cycles.logistics?.deadline_turn || '-'}
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      </header>

      {showHelp && (
        <div className="bg-blue-900/30 border-b border-blue-700/50 px-4 py-1.5 text-xs shrink-0 backdrop-blur-sm">
          <span className="font-bold text-blue-300">遊び方: </span>
          <span>クリック→命令→ターン進行 | ズーム: Ctrl+ホイール or ボタン</span>
          <span className="ml-3 text-gray-400">| ショートカット: Z=リセット L=凡例 H=ヘルプ M=モード P=PhaseLine B=Boundary A=Airspace 矢印=パン +/-=ズーム</span>
        </div>
      )}

      {/* Main: 3 columns */}
      <div className="flex-1 flex flex-nowrap overflow-hidden">
        {/* Left: Units - expanded to 240px */}
        <div className="bg-gray-800/90 border-r border-gray-700/50 p-3 flex flex-col shrink-0 overflow-y-auto backdrop-blur-sm" style={{ width: '320px', minWidth: '320px', maxWidth: '320px' }}>
          <h3 className="font-bold text-sm mb-3 text-blue-300 border-b border-gray-700/50 pb-2">{t('game.unitSection')}</h3>
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
                  <span className={unit.side === 'player' ? 'text-blue-400' : 'text-red-400'}>{unit.side === 'player' ? t('symbols.friend') : t('symbols.enemy')}</span>
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
            role="application"
            aria-label={`Operational map - Zoom: ${Math.round(zoom * 100)}%, Pan: ${pan.x}, ${pan.y}. Use arrow keys to pan, +/- to zoom, Z to reset.`}
          >
            <svg
              viewBox={`0 0 ${GRID_WIDTH} ${GRID_HEIGHT}`}
              className="w-full h-full"
              role="img"
              aria-label={`Tactical map showing ${gameState.units?.length || 0} units`}
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
              {/* Issue #52: Reachable positions preview (movement range) */}
              {reachablePositions.map((pos, i) => (
                <circle
                  key={`reachable-${i}`}
                  cx={pos.x + 0.5}
                  cy={pos.y + 0.5}
                  r="0.35"
                  fill={pos.can_reach ? "none" : "none"}
                  stroke={pos.can_reach ? "#22c55e" : "#ef4444"}
                  strokeWidth="0.08"
                  strokeDasharray="0.15,0.1"
                  opacity="0.6"
                />
              ))}
              {/* Units - use memoized UnitMarker component */}
              {unitList.map((unit) => (
                <UnitMarker key={unit.id} unit={unit} selectedUnitId={selectedUnit?.id || null} onSelect={handleUnitSelect} showExactPosition={showExactPosition} />
              ))}
              {/* Control Measures - Phase Lines */}
              {layerVisibility.phaseLines && (gameState as any)?.control_measures?.phase_lines?.map((pl: PhaseLineType) => (
                <g key={`pl-${pl.id}`}>
                  <path
                    d={getPhaseLinePath(pl.points as any)}
                    stroke={pl.status === 'reported' ? CONTROL_MEASURE_COLORS.phaseLine.reported : pl.status === 'contact' ? CONTROL_MEASURE_COLORS.phaseLine.contact : CONTROL_MEASURE_COLORS.phaseLine.lost}
                    strokeWidth="0.15"
                    fill="none"
                    strokeDasharray={getControlMeasureDashArray(pl.line_style)}
                  />
                  <text x={pl.points[0]?.x || 0} y={(pl.points[0]?.y || 0) - 0.3} fontSize="0.4" fill={pl.status === 'reported' ? CONTROL_MEASURE_COLORS.phaseLine.reported : pl.status === 'contact' ? CONTROL_MEASURE_COLORS.phaseLine.contact : CONTROL_MEASURE_COLORS.phaseLine.lost} fontWeight="bold">
                    {pl.name}
                  </text>
                </g>
              ))}
              {/* Control Measures - Boundaries */}
              {layerVisibility.boundaries && (gameState as any)?.control_measures?.boundaries?.map((b: BoundaryType) => (
                <g key={`boundary-${b.id}`}>
                  <path
                    d={getBoundaryPath(b.points as any)}
                    stroke={b.owning_side === 'player' ? CONTROL_MEASURE_COLORS.boundary.player : b.owning_side === 'enemy' ? CONTROL_MEASURE_COLORS.boundary.enemy : CONTROL_MEASURE_COLORS.boundary.neutral}
                    strokeWidth="0.12"
                    fill="none"
                    strokeDasharray={getControlMeasureDashArray(b.line_style)}
                  />
                </g>
              ))}
              {/* Control Measures - Airspaces */}
              {layerVisibility.airspaces && (gameState as any)?.control_measures?.airspaces?.map((as: AirspaceType) => (
                <g key={`airspace-${as.id}`}>
                  <path
                    d={getAirspacePath(as.points as any)}
                    stroke={as.type === 'air_corridor' ? CONTROL_MEASURE_COLORS.airspace.air_corridor : as.type === 'restricted' ? CONTROL_MEASURE_COLORS.airspace.restricted : as.type === 'ada_zone' ? CONTROL_MEASURE_COLORS.airspace.ada_zone : CONTROL_MEASURE_COLORS.airspace.no_fly}
                    strokeWidth="0.1"
                    fill={as.type === 'air_corridor' ? `${CONTROL_MEASURE_COLORS.airspace.air_corridor}20` : as.type === 'restricted' ? `${CONTROL_MEASURE_COLORS.airspace.restricted}20` : as.type === 'ada_zone' ? `${CONTROL_MEASURE_COLORS.airspace.ada_zone}20` : `${CONTROL_MEASURE_COLORS.airspace.no_fly}20`}
                    fillRule="evenodd"
                  />
                </g>
              ))}
            </svg>
          </div>

          {/* Layer Toggle Controls (top-left) */}
          <div className="absolute top-3 left-3 bg-gray-900/80 backdrop-blur p-2 rounded-lg text-xs border border-gray-700/50 z-10 flex gap-2" role="group" aria-label="Map layers">
            <span className="text-gray-400 font-medium mr-1" id="layers-label">{t('game.layers')}:</span>
            <button onClick={() => setLayerVisibility(v => ({ ...v, phaseLines: !v.phaseLines }))} aria-pressed={layerVisibility.phaseLines} aria-labelledby="layers-label" className={`px-2 py-1 rounded transition-colors ${layerVisibility.phaseLines ? 'bg-green-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="Phase Lines (P key)">
              PL
            </button>
            <button onClick={() => setLayerVisibility(v => ({ ...v, boundaries: !v.boundaries }))} aria-pressed={layerVisibility.boundaries} aria-labelledby="layers-label" className={`px-2 py-1 rounded transition-colors ${layerVisibility.boundaries ? 'bg-blue-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="Boundaries (B key)">
              Bdy
            </button>
            <button onClick={() => setLayerVisibility(v => ({ ...v, airspaces: !v.airspaces }))} aria-pressed={layerVisibility.airspaces} aria-labelledby="layers-label" className={`px-2 py-1 rounded transition-colors ${layerVisibility.airspaces ? 'bg-cyan-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="Airspace (A key)">
              Air
            </button>
          </div>

          {/* Map Controls (outside clipped area) - modern glass style */}
          <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
            <button onClick={handleZoomIn} aria-label="マップをzoom in" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">+</button>
            <button onClick={handleZoomOut} aria-label="マップをzoom out" className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-lg font-bold transition-colors border border-gray-600/30">−</button>
            <button onClick={handleZoomReset} aria-label={t('game.resetZoom')} className="w-9 h-9 bg-gray-700/80 hover:bg-gray-600/80 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30">{t('common.zoomReset')}</button>
            <button onClick={() => setShowExactPosition(!showExactPosition)} aria-label={t('game.fowDebug')} aria-pressed={showExactPosition} className={`w-9 h-9 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30 ${showExactPosition ? 'bg-purple-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="FoW debug: Show exact positions">
              FoW
            </button>
            <button onClick={() => setShowLegend(!showLegend)} aria-label={t('game.legend')} aria-pressed={showLegend} className={`w-9 h-9 backdrop-blur rounded-lg text-xs font-medium transition-colors border border-gray-600/30 ${showLegend ? 'bg-cyan-600/80 text-white' : 'bg-gray-700/80 text-gray-400'}`} title="Legend">
              {t('game.legend')}
            </button>
          </div>

          {/* Map Info - modern style */}
          <div className="absolute bottom-3 left-3 bg-gray-900/80 backdrop-blur p-2 rounded-lg text-xs border border-gray-700/50 z-10 flex gap-4">
            <span className="text-blue-400 font-medium">{t('symbols.friend')}: {gameState.units.filter(u => u.side === 'player').length}</span>
            <span className="text-red-400 font-medium">{t('symbols.enemy')}: {gameState.units.filter(u => u.side === 'enemy').length}</span>
            <span className="text-gray-400">{t('game.zoom')}: {Math.round(zoom * 100)}%</span>
          </div>

          {/* Legend Panel - Issue #41 */}
          {showLegend && (
            <div className="absolute top-3 left-3 bg-gray-900/95 backdrop-blur p-3 rounded-lg text-xs border border-cyan-700/50 z-20 shadow-xl">
              <div className="font-bold text-cyan-300 mb-2 border-b border-gray-700/50 pb-1">{t('game.legend')}</div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-blue-500"></div>
                  <span className="text-gray-300">{t('symbols.friend')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-500"></div>
                  <span className="text-gray-300">{t('symbols.enemy')}</span>
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
              <div className="font-bold text-purple-300 mb-1 text-center">{t('game.battleOddsTitle')}</div>
              <div className="flex items-center justify-center gap-3">
                <span className="text-blue-400 font-medium">{battleOdds.attacker}</span>
                <span className="text-gray-400">vs</span>
                <span className="text-red-400 font-medium">{battleOdds.defender}</span>
              </div>
              <div className={`text-center font-bold mt-1 ${
                battleOdds.odds === t('battleOdds.advantageous') ? 'text-green-400' :
                battleOdds.odds === t('battleOdds.slightlyAdvantageous') ? 'text-lime-400' :
                battleOdds.odds === t('battleOdds.even') ? 'text-yellow-400' :
                battleOdds.odds === t('battleOdds.slightlyDisadvantageous') ? 'text-orange-400' :
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
              <div className="text-gray-400 text-[10px]">{t('game.clickForInfo')}</div>
            </div>
          )}
        </div>

        {/* Right: Orders + Logs - expanded to 320px */}
        <div className="bg-gray-800/90 border-l border-gray-700/50 flex flex-col shrink-0 overflow-hidden backdrop-blur-sm" style={{ width: '400px', minWidth: '400px', maxWidth: '400px' }}>
          {/* Tab system - CPX 4 tabs */}
          <div className="flex border-b border-gray-700/50 shrink-0">
            <button onClick={() => { setActiveTab('plan'); fetchOpord(); }} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'plan' ? 'text-green-300 border-green-500 bg-green-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>PLAN</button>
            <button onClick={() => setActiveTab('sync')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'sync' ? 'text-purple-300 border-purple-500 bg-purple-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>SYNC</button>
            <button onClick={() => setActiveTab('situation')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'situation' ? 'text-cyan-300 border-cyan-500 bg-cyan-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>SITUATION</button>
            <button onClick={() => setActiveTab('sustain')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'sustain' ? 'text-orange-300 border-orange-500 bg-orange-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>SUSTAIN</button>
            <button onClick={() => setActiveTab('chat')} className={`flex-1 p-2 text-xs font-bold border-b-2 transition-colors ${activeTab === 'chat' ? 'text-pink-300 border-pink-500 bg-pink-900/20' : 'text-gray-400 hover:text-gray-300 border-transparent'}`}>CHAT</button>
          </div>

          {/* SITREP Card - shown on info tab */}
          {activeTab === 'situation' && sitrep && (
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
                      {section.type === 'overview' && t('sections.overview')}
                      {section.type === 'unit_status' && t('sections.unitStatus')}
                      {section.type === 'enemy_activity' && t('sections.enemyActivity')}
                      {section.type === 'logistics' && t('sections.logistics')}
                      {section.type === 'orders_result' && t('sections.ordersResult')}
                      {section.type === 'friction' && t('sections.friction')}
                      {section.type === 'command' && t('sections.command')}
                    </div>
                    <div className="text-gray-200 line-clamp-2">{section.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SITREP History - previous sitreps */}
          {activeTab === 'situation' && sitrepHistory.length > 0 && (
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
          {activeTab === 'situation' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              <h3 className="font-bold text-sm mb-3 text-cyan-300 border-b border-gray-700/50 pb-2">{t('game.sitrepHistory')}</h3>
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
                <p className="text-gray-500 text-xs">{t('game.noHistory')}</p>
              )}
            </div>
          )}

          {/* OPORD Tab - SMESC format */}
          {activeTab === 'plan' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold text-sm text-green-300 border-b border-gray-700/50 pb-2">■ OPORD/FRAGO (SMESC)</h3>
                <button
                  onClick={() => setOpordEditMode(!opordEditMode)}
                  className="text-xs px-2 py-1 bg-green-700/50 hover:bg-green-600/50 rounded text-green-300"
                >
                  {opordEditMode ? '閉じる' : '編集'}
                </button>
              </div>

              {opordLoading ? (
                <LoadingDisplay message="OPORD読み込み中..." className="py-4" />
              ) : opordData ? (
                <div className="space-y-3 text-xs">
                  {/* Header */}
                  <div className="bg-gray-800/50 rounded p-2 border border-gray-700/30">
                    <div className="font-bold text-green-300 text-sm">{opordData.title || '作戦計画'}</div>
                    <div className="text-gray-400 text-[10px] mt-1">
                      区分: {opordData.classification || 'unclassified'} | 発効日: {opordData.effective_date || '-'}
                    </div>
                  </div>

                  {/* Situation */}
                  <div className="bg-gray-800/50 rounded p-2 border border-gray-700/30">
                    <div className="font-bold text-yellow-300 mb-1">SITUATION（状況）</div>
                    {opordEditMode ? (
                      <div className="space-y-2">
                        <textarea
                          value={opordData.situation?.enemy_situation || ''}
                          onChange={(e) => setOpordData({...opordData, situation: {...opordData.situation, enemy_situation: e.target.value}})}
                          className="w-full bg-gray-900/50 rounded p-1 text-gray-300 text-[10px] h-12"
                          placeholder={t('game.enemySituation')}
                        />
                        <textarea
                          value={opordData.situation?.friendly_situation || ''}
                          onChange={(e) => setOpordData({...opordData, situation: {...opordData.situation, friendly_situation: e.target.value}})}
                          className="w-full bg-gray-900/50 rounded p-1 text-gray-300 text-[10px] h-12"
                          placeholder={t('game.friendlySituation')}
                        />
                      </div>
                    ) : (
                      <div className="space-y-1 text-gray-300">
                        <div><span className="text-gray-500">敵:</span> {opordData.situation?.enemy_situation || '-'}</div>
                        <div><span className="text-gray-500">味方:</span> {opordData.situation?.friendly_situation || '-'}</div>
                        <div><span className="text-gray-500">地形:</span> {opordData.situation?.terrain_impact || '-'}</div>
                        <div><span className="text-gray-500">天候:</span> {opordData.situation?.weather_impact || '-'}</div>
                      </div>
                    )}
                  </div>

                  {/* Mission */}
                  <div className="bg-gray-800/50 rounded p-2 border border-gray-700/30">
                    <div className="font-bold text-yellow-300 mb-1">MISSION（任務）</div>
                    {opordEditMode ? (
                      <div className="space-y-2">
                        <textarea
                          value={opordData.mission?.task || ''}
                          onChange={(e) => setOpordData({...opordData, mission: {...opordData.mission, task: e.target.value}})}
                          className="w-full bg-gray-900/50 rounded p-1 text-gray-300 text-[10px] h-12"
                          placeholder={t('game.mission')}
                        />
                      </div>
                    ) : (
                      <div className="space-y-1 text-gray-300">
                        <div><span className="text-gray-500">任務:</span> {opordData.mission?.task || '-'}</div>
                        <div><span className="text-gray-500">目的:</span> {opordData.mission?.purpose || '-'}</div>
                        <div><span className="text-gray-500">終結:</span> {opordData.mission?.end_state || '-'}</div>
                      </div>
                    )}
                  </div>

                  {/* Execution */}
                  <div className="bg-gray-800/50 rounded p-2 border border-gray-700/30">
                    <div className="font-bold text-yellow-300 mb-1">EXECUTION（実行）</div>
                    {opordEditMode ? (
                      <div className="space-y-2">
                        <textarea
                          value={opordData.execution?.concept_of_operations || ''}
                          onChange={(e) => setOpordData({...opordData, execution: {...opordData.execution, concept_of_operations: e.target.value}})}
                          className="w-full bg-gray-900/50 rounded p-1 text-gray-300 text-[10px] h-16"
                          placeholder={t('game.operationConcept')}
                        />
                      </div>
                    ) : (
                      <div className="space-y-1 text-gray-300">
                        <div><span className="text-gray-500">構想:</span> {opordData.execution?.concept_of_operations || '-'}</div>
                        <div><span className="text-gray-500">調整:</span> {opordData.execution?.coordination || '-'}</div>
                        <div><span className="text-gray-500">通信:</span> {opordData.execution?.command_signal || '-'}</div>
                      </div>
                    )}
                  </div>

                  {/* Coordination */}
                  <div className="bg-gray-800/50 rounded p-2 border border-gray-700/30">
                    <div className="font-bold text-yellow-300 mb-1">COORDINATION（調整）</div>
                    {opordEditMode ? (
                      <div className="space-y-2">
                        <textarea
                          value={opordData.coordination?.fire_support || ''}
                          onChange={(e) => setOpordData({...opordData, coordination: {...opordData.coordination, fire_support: e.target.value}})}
                          className="w-full bg-gray-900/50 rounded p-1 text-gray-300 text-[10px] h-12"
                          placeholder={t('game.fireSupport')}
                        />
                      </div>
                    ) : (
                      <div className="space-y-1 text-gray-300">
                        <div><span className="text-gray-500">火力:</span> {opordData.coordination?.fire_support || '-'}</div>
                        <div><span className="text-gray-500">航空:</span> {opordData.coordination?.air_support || '-'}</div>
                        <div><span className="text-gray-500">指揮:</span> {opordData.coordination?.c2_relationships || '-'}</div>
                      </div>
                    )}
                  </div>

                  {/* Service Support */}
                  <div className="bg-gray-800/50 rounded p-2 border border-gray-700/30">
                    <div className="font-bold text-yellow-300 mb-1">SERVICE SUPPORT（後方支援）</div>
                    {opordEditMode ? (
                      <div className="space-y-2">
                        <textarea
                          value={opordData.service_support?.supply?.ammo || ''}
                          onChange={(e) => setOpordData({...opordData, service_support: {...opordData.service_support, supply: {...opordData.service_support?.supply, ammo: e.target.value}}})}
                          className="w-full bg-gray-900/50 rounded p-1 text-gray-300 text-[10px] h-12"
                          placeholder={t('game.ammunition')}
                        />
                      </div>
                    ) : (
                      <div className="space-y-1 text-gray-300">
                        <div><span className="text-gray-500">弾薬:</span> {opordData.service_support?.supply?.ammo || '-'}</div>
                        <div><span className="text-gray-500">燃料:</span> {opordData.service_support?.supply?.fuel || '-'}</div>
                        <div><span className="text-gray-500">整備:</span> {opordData.service_support?.maintenance || '-'}</div>
                        <div><span className="text-gray-500">衛生:</span> {opordData.service_support?.medical || '-'}</div>
                      </div>
                    )}
                  </div>

                  {/* Save Button */}
                  {opordEditMode && (
                    <button
                      onClick={() => updateOpord(opordData)}
                      className="w-full py-2 bg-green-600 hover:bg-green-500 rounded text-white text-xs font-bold"
                    >
                      保存
                    </button>
                  )}
                </div>
              ) : (
                <p className="text-gray-500 text-xs">OPORDがありません。「編集」ボタンで作成してください。</p>
              )}
            </div>
          )}

          {/* Reports Tab - CPX-REPORTS */}

          {/* SYNC Tab - Synchronization Matrix (Mock) */}
          {activeTab === 'sync' && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              <h3 className="font-bold text-sm text-purple-300 border-b border-gray-700/50 pb-2">■ SYNCHRONIZATION MATRIX</h3>

              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-purple-300 mb-2">FIRE SUPPORT COORDINATION</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-400">Artillery:</span><span className="text-green-400">Available</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Air Strike:</span><span className="text-yellow-400">On Call</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Naval Fire:</span><span className="text-red-400">Unavailable</span></div>
                </div>
              </div>

              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-purple-300 mb-2">MOVEMENT SYNCHRONIZATION</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-400">Phase Line A:</span><span className="text-green-400">Cleared</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Phase Line B:</span><span className="text-yellow-400">In Progress</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Objective:</span><span className="text-gray-400">Pending</span></div>
                </div>
              </div>

              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-purple-300 mb-2">C2 RELATIONSHIPS</div>
                <div className="space-y-1 text-xs">
                  <div><span className="text-gray-400">Higher HQ:</span> Corps</div>
                  <div><span className="text-gray-400">Left:</span> 3rd Bde</div>
                  <div><span className="text-gray-400">Right:</span> 5th Bde</div>
                </div>
              </div>
            </div>
          )}

          {/* SUSTAIN Tab - Logistics (Mock) */}
          {activeTab === 'sustain' && gameState && (
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              <h3 className="font-bold text-sm text-orange-300 border-b border-gray-700/50 pb-2">■ LOGISTICS STATUS</h3>

              {/* Ammunition */}
              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-orange-300 mb-2">AMMUNITION</div>
                <div className="space-y-2 text-xs">
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-gray-400"> Artillery (HE):</span><span className="text-green-400">75%</span></div>
                    <div className="w-full h-2 bg-gray-700 rounded-full"><div className="h-full bg-green-500 rounded-full" style={{width: '75%'}}></div></div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-gray-400"> Artillery (Illum):</span><span className="text-yellow-400">45%</span></div>
                    <div className="w-full h-2 bg-gray-700 rounded-full"><div className="h-full bg-yellow-500 rounded-full" style={{width: '45%'}}></div></div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-gray-400"> Small Arms:</span><span className="text-green-400">90%</span></div>
                    <div className="w-full h-2 bg-gray-700 rounded-full"><div className="h-full bg-green-500 rounded-full" style={{width: '90%'}}></div></div>
                  </div>
                </div>
              </div>

              {/* Fuel */}
              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-orange-300 mb-2">FUEL</div>
                <div className="space-y-2 text-xs">
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-gray-400"> Motor Transport:</span><span className="text-green-400">80%</span></div>
                    <div className="w-full h-2 bg-gray-700 rounded-full"><div className="h-full bg-green-500 rounded-full" style={{width: '80%'}}></div></div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-gray-400"> Armor:</span><span className="text-yellow-400">55%</span></div>
                    <div className="w-full h-2 bg-gray-700 rounded-full"><div className="h-full bg-yellow-500 rounded-full" style={{width: '55%'}}></div></div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-gray-400"> Aviation:</span><span className="text-green-400">70%</span></div>
                    <div className="w-full h-2 bg-gray-700 rounded-full"><div className="h-full bg-green-500 rounded-full" style={{width: '70%'}}></div></div>
                  </div>
                </div>
              </div>

              {/* Maintenance */}
              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-orange-300 mb-2">MAINTENANCE</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-400"> Equipment Ready:</span><span className="text-green-400">85%</span></div>
                  <div className="flex justify-between"><span className="text-gray-400"> Under Repair:</span><span className="text-yellow-400">12%</span></div>
                  <div className="flex justify-between"><span className="text-gray-400"> Await Parts:</span><span className="text-red-400">3%</span></div>
                </div>
              </div>

              {/* Casualties */}
              <div className="bg-gray-800/50 rounded p-3 border border-gray-700/30">
                <div className="font-bold text-xs text-orange-300 mb-2">CASUALTIES</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-400"> KIA:</span><span className="text-red-400">12</span></div>
                  <div className="flex justify-between"><span className="text-gray-400"> WIA:</span><span className="text-yellow-400">34</span></div>
                  <div className="flex justify-between"><span className="text-gray-400"> MIA:</span><span className="text-gray-400">2</span></div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'situation' && gameId && (
            <div className="flex-1 overflow-y-auto">
              <ReportPanel gameId={gameId} turn={gameState?.turn || 1} />
            </div>
          )}

          {activeTab === 'chat' && gameId && (
            <div className="flex-1 overflow-hidden">
              <ChatPanel gameId={gameId} userRole="blue" />
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
                // Arcade mode: 6 command buttons with batch support
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
                      <button key={btn.cmd} onClick={() => addToBatch(btn.cmd)} disabled={loading || !selectedUnit}
                        className={`${btn.color} hover:opacity-90 disabled:opacity-50 rounded-lg p-2 text-xs font-bold transition-all flex flex-col items-center gap-0.5`}>
                        <span className="text-sm">{btn.icon}</span>
                        <span>{btn.label}</span>
                      </button>
                    ))}
                  </div>
                  {/* Issue #56: Pending orders panel */}
                  {pendingOrders.length > 0 && (
                    <div className="mt-2 bg-purple-900/30 rounded-lg p-2 text-xs space-y-1">
                      <div className="text-purple-300 font-medium flex justify-between items-center">
                        <span>保留中の命令: {pendingOrders.length}</span>
                        <button onClick={() => setPendingOrders([])} className="text-gray-400 hover:text-white text-[10px]">クリア</button>
                      </div>
                      {pendingOrders.map((order, i) => {
                        const unit = gameState?.units?.find(u => u.id === order.unit_id);
                        return (
                          <div key={i} className="flex justify-between text-gray-300 text-[10px] bg-gray-800/50 rounded px-2 py-1">
                            <span>{unit?.name || `Unit ${order.unit_id}`}</span>
                            <span className="text-purple-400">{order.order_type}</span>
                          </div>
                        );
                      })}
                      <button onClick={submitBatchOrders} disabled={loading}
                        className="w-full mt-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 rounded-lg p-2 text-xs font-bold transition-colors">
                        一括送信 ({pendingOrders.length})
                      </button>
                    </div>
                  )}
                  {/* STRIKE tokens display for selected unit */}
                  {selectedUnit && gameMode === 'arcade' && 'strike_remaining' in selectedUnit && (
                    <div className="mt-2 flex items-center gap-2 text-xs">
                      <span className="text-purple-300">特攻:</span>
                      <div className="flex gap-1">
                        {Array.from({ length: 3 }).map((_, i) => (
                          <span key={i} className={`w-3 h-3 rounded-full ${i < ((selectedUnit as any).strike_remaining || 0) ? 'bg-purple-500' : 'bg-gray-600'}`} />
                        ))}
                      </div>
                      {(selectedUnit as any).strike_next_attack_blocked && (
                        <span className="text-red-400 text-[10px]">(次ターン攻撃不可)</span>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                // Classic mode: text input
                <>
                  <textarea value={orderInput} onChange={(e) => setOrderInput(e.target.value)}
                    placeholder="命令を入力..." className="w-full bg-gray-700/50 border border-gray-600/50 rounded-lg p-2 text-xs h-16 mb-2 focus:border-blue-500 focus:outline-none backdrop-blur" />
                  <div className="flex gap-2">
                    <button onClick={parseOrder} disabled={loading || !orderInput.trim()} aria-label={t('game.parseOrder')} className="flex-1 bg-blue-600/80 hover:bg-blue-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">{t('commands.parse')}</button>
                    {parsedOrder && (
                      <button onClick={submitOrder} disabled={loading} aria-label={t('game.submitOrder')} className="flex-1 bg-green-600/80 hover:bg-green-600 disabled:bg-gray-600/50 rounded-lg p-2 text-xs font-medium transition-colors">{t('commands.submit')}</button>
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
            <h3 className="font-bold text-sm mb-3 text-blue-300 border-b border-gray-700/50 pb-2">■ 戦闘ログ {activeTab === 'sync' || activeTab === 'situation' ? '(最新3件)' : '(全履歴)'}</h3>
            {turnLogs.length > 0 ? (
              <div className="space-y-3 text-xs">
                {((activeTab === 'sync' || activeTab === 'situation') ? turnLogs.slice(-3) : turnLogs).map((log, idx) => (
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
            <button onClick={advanceTurn} disabled={loading} aria-label={t('game.advanceTurn')} className="w-full bg-purple-600/80 hover:bg-purple-600 disabled:bg-gray-600/50 rounded-lg p-3 text-sm font-bold transition-all shadow-lg shadow-purple-900/30">
              ▶ {t('commands.advanceTurn')}
            </button>
            <button onClick={endGame} aria-label={t('game.endGame')} className="w-full bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 rounded-lg p-2 text-xs font-medium transition-colors">
              {t('debriefing.title')}
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
