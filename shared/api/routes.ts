// API Routes - Centralized API endpoint definitions
// This file defines all API endpoints used by the application.
// Both frontend and backend should use these definitions for consistency.

import type { Game, Unit, Sitrep, ParsedOrder, AdjudicationResult } from "../types";

// API Base URL - should be set via environment variable
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper to convert ID to string
const toId = (id: string | number): string => String(id);

// Route path templates - use these to build actual URLs
export const ROUTES = {
  // Game endpoints (standard: /api/games/...)
  GAMES_LIST: "/api/games/",
  GAME_DETAIL: (gameId: string | number) => `/api/games/${toId(gameId)}`,
  GAME_STATE: (gameId: string | number) => `/api/games/${toId(gameId)}/state`,
  GAME_UNITS: (gameId: string | number) => `/api/games/${toId(gameId)}/units`,
  GAME_SITREP: (gameId: string | number) => `/api/games/${toId(gameId)}/sitrep`,
  GAME_DEBRIEFING: (gameId: string | number) => `/api/games/${toId(gameId)}/debriefing`,
  GAME_START: "/api/games/start",
  GAME_END: (gameId: string | number) => `/api/games/${toId(gameId)}/end`,

  // Unit endpoints
  UNIT_CREATE: (gameId: string | number) => `/api/games/${toId(gameId)}/units/`,
  UNIT_MOVE: (unitId: string | number) => `/api/units/${toId(unitId)}/move`,

  // Order endpoints
  ORDER_PARSE: "/api/parse-order",
  ORDER_CREATE: "/api/orders/",
  TURN_ADVANCE: "/api/advance-turn",

  // Scenario endpoints
  SCENARIOS_LIST: "/api/scenarios",
  SCENARIO_DETAIL: (scenarioId: string) => `/api/scenarios/${scenarioId}`,

  // Internal/Debug endpoints (for admin/debug use only)
  INTERNAL_TRUE_STATE: (gameId: string | number) => `/api/internal/games/${toId(gameId)}/true-state`,
  INTERNAL_UNITS: (gameId: string | number) => `/api/internal/games/${toId(gameId)}/units`,
} as const;

// Type definitions for API responses
export interface GameListItem {
  id: number;
  name: string;
  current_turn: number;
  current_date: string;
  current_time: string;
  weather: string;
  phase: string;
  is_active: boolean;
}

export interface GameDetail extends GameListItem {
  terrain_data: unknown;
  map_width: number;
  map_height: number;
}

export interface GameStartRequest {
  scenario_id: string;
  game_name: string;
}

export interface GameStartResponse {
  id: number;
  name: string;
  current_turn: number;
  current_time: string;
  weather: string;
  phase: string;
  is_active: boolean;
  map_width: number;
  map_height: number;
}

export interface OrderCreateRequest {
  unit_id: number;
  order_type: string;
  target_units?: number[] | null;
  intent: string;
  location_x?: number | null;
  location_y?: number | null;
  location_name?: string | null;
  priority: "high" | "normal" | "low";
}

export interface OrderCreateResponse {
  id: number;
  order_type: string;
  intent: string;
  status: string;
}

export interface OrderParseRequest {
  player_input: string;
  game_id: number;
}

export interface TurnAdvanceRequest {
  game_id: number;
}

export interface TurnAdvanceResponse {
  turn: number;
  results: unknown[];
  events: unknown[];
  enemy_results: unknown[];
  sitrep: unknown;
  next_time: string;
}

export interface MoveUnitRequest {
  x: number;
  y: number;
}

export interface MoveUnitResponse {
  success: boolean;
  unit_id: number;
  x: number;
  y: number;
}

export interface EndGameRequest {
  game_id: number;
}

export interface EndGameResponse {
  success: boolean;
  game_id: number;
  message: string;
}

// API client functions
export const api = {
  baseUrl: API_BASE_URL,

  // Game operations
  games: {
    list: () => fetch(ROUTES.GAMES_LIST).then((r) => r.json() as Promise<GameListItem[]>),
    get: (gameId: string | number) =>
      fetch(ROUTES.GAME_DETAIL(gameId)).then((r) => r.json() as Promise<GameDetail>),
    start: (request: GameStartRequest) =>
      fetch(ROUTES.GAME_START, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then((r) => r.json() as Promise<GameStartResponse>),
    end: (gameId: string | number, request: EndGameRequest) =>
      fetch(ROUTES.GAME_END(gameId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then((r) => r.json() as Promise<EndGameResponse>),
    getState: (gameId: string | number) =>
      fetch(ROUTES.GAME_STATE(gameId)).then((r) => r.json()),
    getUnits: (gameId: string | number) =>
      fetch(ROUTES.GAME_UNITS(gameId)).then((r) => r.json()),
    getSitrep: (gameId: string | number) =>
      fetch(ROUTES.GAME_SITREP(gameId)).then((r) => r.json()),
    getDebriefing: (gameId: string | number) =>
      fetch(ROUTES.GAME_DEBRIEFING(gameId)).then((r) => r.json()),
  },

  // Unit operations
  units: {
    create: (gameId: string | number, params: Record<string, string | number>) => {
      const query = new URLSearchParams(params as Record<string, string>).toString();
      return fetch(ROUTES.UNIT_CREATE(gameId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      }).then((r) => r.json());
    },
    move: (unitId: string | number, request: MoveUnitRequest) =>
      fetch(ROUTES.UNIT_MOVE(unitId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then((r) => r.json() as Promise<MoveUnitResponse>),
  },

  // Order operations
  orders: {
    parse: (request: OrderParseRequest) =>
      fetch(ROUTES.ORDER_PARSE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then((r) => r.json() as Promise<ParsedOrder>),
    create: (request: OrderCreateRequest) =>
      fetch(ROUTES.ORDER_CREATE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then((r) => r.json() as Promise<OrderCreateResponse>),
  },

  // Turn operations
  turns: {
    advance: (request: TurnAdvanceRequest) =>
      fetch(ROUTES.TURN_ADVANCE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then((r) => r.json() as Promise<TurnAdvanceResponse>),
  },

  // Scenario operations
  scenarios: {
    list: () => fetch(ROUTES.SCENARIOS_LIST).then((r) => r.json()),
    get: (scenarioId: string) => fetch(ROUTES.SCENARIO_DETAIL(scenarioId)).then((r) => r.json()),
  },
};

export default api;
