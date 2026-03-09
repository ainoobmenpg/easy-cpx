// API client utility - centralizes API URL management
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  gameStart: `${API_BASE_URL}/api/games/start`,
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
};

export default API;
