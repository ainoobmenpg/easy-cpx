// API client utility - centralizes API URL management
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to convert ID to string
const toId = (id: string | number): string => String(id);

export const API = {
  baseUrl: API_BASE_URL,

  // Game endpoints
  games: `${API_BASE_URL}/api/games`,
  gameState: (gameId: string | number) => `${API_BASE_URL}/api/game/${toId(gameId)}/state`,
  gameUnits: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/units`,
  createUnit: (gameId: string | number) => `${API_BASE_URL}/api/games/${toId(gameId)}/units/`,
  gameSitrep: (gameId: string | number) => `${API_BASE_URL}/api/game/${toId(gameId)}/sitrep`,
  gameDebriefing: (gameId: string | number) => `${API_BASE_URL}/api/game/${toId(gameId)}/debriefing`,
  gameStart: `${API_BASE_URL}/api/game/start`,
  gameEnd: `${API_BASE_URL}/api/game/end`,

  // Order endpoints
  parseOrder: `${API_BASE_URL}/api/parse-order`,
  orders: `${API_BASE_URL}/api/orders/`,
  advanceTurn: `${API_BASE_URL}/api/advance-turn`,

  // Unit endpoints
  moveUnit: (unitId: string | number) => `${API_BASE_URL}/api/units/${toId(unitId)}/move`,

  // Scenario endpoints
  scenarios: `${API_BASE_URL}/api/scenarios`,
  scenario: (scenarioId: string) => `${API_BASE_URL}/api/scenarios/${scenarioId}`,
};

export default API;
