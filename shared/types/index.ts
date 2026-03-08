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

export interface Unit {
  id: string;
  name: string;
  type: string;
  x: number;
  y: number;
  status: UnitStatus;
  ammo: SupplyLevel;
  fuel: SupplyLevel;
  readiness: SupplyLevel;
}

export interface GameState {
  turn: number;
  time: string;
  weather: string;
  units: Unit[];
  player_knowledge: Record<string, unknown>;
}
