// API client utility - centralizes API URL management
// Dynamic URL based on current window location to support 127.0.0.1 access
const getApiBaseUrl = (): string => {
  // Get backend port from env, default to 8000
  const backendPort = process.env.NEXT_PUBLIC_API_PORT || '8000';
  if (typeof window !== 'undefined') {
    // Use current window location hostname - supports both localhost and 127.0.0.1
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:${backendPort}`;
  }
  // Fallback for SSR
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

// Helper to convert ID to string
const toId = (id: string | number): string => String(id);

export const API = {
  baseUrl: API_BASE_URL,

  // Game endpoints
  games: `${API_BASE_URL}/api/games/`,
  game: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}`,
  gameState: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/state`,
  gameUnits: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/units`,
  createUnit: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/units/`,
  gameSitrep: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/sitrep`,
  gameDebriefing: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/debriefing`,
  gameStart: `${API_BASE_URL}/api/games/from-scenario`,
  gameEnd: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/end`,

  // Order endpoints
  parseOrder: `${API_BASE_URL}/api/parse-order`,
  orders: `${API_BASE_URL}/api/orders/`,
  advanceTurn: `${API_BASE_URL}/api/advance-turn`,

  // Unit endpoints
  moveUnit: (unitId: string | number) => `${API_BASE_URL}/api/units/${toId(unitId)}/move`,
  unitReachable: (unitId: string | number) => `${API_BASE_URL}/api/units/${toId(unitId)}/reachable`,

  // Turn commit endpoint (batch orders)
  turnCommit: `${API_BASE_URL}/api/turn/commit`,

  // Scenario endpoints
  scenarios: `${API_BASE_URL}/api/scenarios`,
  scenario: (scenarioId: string) => `${API_BASE_URL}/api/scenarios/${scenarioId}`,

  // OPORD/FRAGO endpoints (SMESC format)
  opord: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/opord`,
  opordDisplay: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/opord/display`,

  // Training endpoints
  trainingInitialize: `${API_BASE_URL}/api/training/initialize`,
  trainingUpdate: `${API_BASE_URL}/api/training/update`,
  trainingFinalize: `${API_BASE_URL}/api/training/finalize`,
  trainingMetrics: (gameId: string | number) => `${API_BASE_URL}/api/training/metrics/${toId(gameId)}`,
  trainingSummary: (gameId: string | number) => `${API_BASE_URL}/api/training/summary/${toId(gameId)}`,

  // Replay endpoints
  replayTimeline: (gameId: string | number) => `${API_BASE_URL}/api/replay/${toId(gameId)}/timeline`,
  replayTurn: (gameId: string | number, turnNumber: number) => `${API_BASE_URL}/api/replay/${toId(gameId)}/turn/${turnNumber}`,
  replayState: (gameId: string | number, turnNumber: number) => `${API_BASE_URL}/api/replay/${toId(gameId)}/state/${turnNumber}`,
};

export default API;
