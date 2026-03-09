// Unit Type Enum - unified vocabulary for all unit types
export type UnitType =
  | 'armor'
  | 'infantry'
  | 'atgm'
  | 'sniper'
  | 'scout'
  | 'artillery'
  | 'air_defense'
  | 'attack_helo'
  | 'transport_helo'
  | 'aircraft'
  | 'uav'
  | 'recon'
  | 'support';

// Order Parser Types
export type OrderType = 'move' | 'attack' | 'defend' | 'support' | 'retreat' | 'recon' | 'supply' | 'special';

export interface OrderLocation {
  x: number;
  y: number;
  area_name?: string;
}

export interface OrderParameters {
  priority?: 'high' | 'normal' | 'low';
  formation?: string;
  timing?: string;
}

export interface ParsedOrder {
  order_type: OrderType;
  target_units: string[];
  intent: string;
  location?: OrderLocation;
  parameters?: OrderParameters;
  assumptions?: string[];
}

// Adjudication Types
export type OrderOutcome = 'success' | 'partial' | 'failed' | 'blocked' | 'cancelled';

export interface StateChange {
  type: string;
  target: string;
  field: string;
  old_value: unknown;
  new_value: unknown;
}

export interface OrderResult {
  order_id: string;
  outcome: OrderOutcome;
  changes: StateChange[];
  reason?: string;
}

export interface AdjudicationEvent {
  type: string;
  turn: number;
  data: Record<string, unknown>;
}

export interface AdjudicationResult {
  turn: number;
  results: OrderResult[];
  events: AdjudicationEvent[];
  fog_updates?: string[];
}

// SITREP Types
export type SitrepSectionType = 'overview' | 'unit_status' | 'enemy_activity' | 'logistics' | 'orders_result' | 'friction' | 'command';
export type ConfidenceLevel = 'confirmed' | 'estimated' | 'unknown';

export interface SitrepSection {
  type: SitrepSectionType;
  content: string;
  confidence: ConfidenceLevel;
}

export interface MapUpdate {
  x: number;
  y: number;
  type: string;
  visibility: ConfidenceLevel;
}

export interface Sitrep {
  turn: number;
  timestamp: string;
  sections: SitrepSection[];
  map_updates?: MapUpdate[];
}

// Game State Types
export type UnitStatus = 'intact' | 'light_damage' | 'medium_damage' | 'heavy_damage' | 'destroyed';
export type SupplyLevel = 'full' | 'depleted' | 'exhausted';

// Extended Unit interface for frontend (with FoW fields)
export interface Unit {
  id: number;
  name: string;
  type: string;
  side: 'player' | 'enemy';
  x: number;
  y: number;
  status: UnitStatus;
  ammo: SupplyLevel;
  fuel: SupplyLevel;
  readiness: SupplyLevel;
  strength: number;
  infantry_subtype?: string;
  recon_value?: number;
  visibility_range?: number;
  // Fog of War fields
  observation_confidence?: ConfidenceLevel;
  last_observed_turn?: number;
  confidence_score?: number;
  estimated_x?: number;
  estimated_y?: number;
  position_accuracy?: number;
  last_known_type?: string;
  observation_sources?: Array<{ observer_id: number; confidence: number }>;
}

// Game State interface for frontend
export interface TerrainInfo {
  symbol: string;
  color: string;
  name: string;
}

export interface WeatherEffects {
  reconnaissance_modifier: number;
  movement_modifier: number;
  [key: string]: unknown;
}

export interface GameState {
  game_id: number;
  turn: number;
  time: string;
  date: string;
  weather: string;
  phase: string;
  is_night: boolean;
  terrain: Record<string, string>;
  terrain_info: Record<string, TerrainInfo>;
  weather_effects: WeatherEffects;
  units: Unit[];
  player_knowledge?: Record<string, unknown>;
  // Arcade mode scoring
  score?: {
    player: number;
    enemy: number;
  };
}

// Turn Log types for frontend
export interface TurnLogOrder {
  unit: string;
  outcome: string;
}

export interface TurnLog {
  turn: number;
  orders: TurnLogOrder[];
}

// API Response types
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
  terrain_data?: Record<string, string>;
  map_width: number;
  map_height: number;
}

// Order submission types
export interface OrderSubmit {
  unit_id: number;
  order_type: OrderType;
  target_units?: number[];
  intent: string;
  location_x?: number;
  location_y?: number;
  location_name?: string;
  priority?: 'high' | 'normal' | 'low';
}

// Turn advance types
export interface TurnAdvanceRequest {
  game_id: number;
}

export interface TurnAdvanceResponse {
  turn: number;
  results: OrderResult[];
  events: AdjudicationEvent[];
  enemy_results: unknown[];
  sitrep: Sitrep;
  next_time: string;
}
