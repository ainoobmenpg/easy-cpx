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
  // C2: Multi-national support
  faction?: string;      // National faction (e.g., "US", "GER", "UK", "OPFOR")
  echelon?: string;      // Unit echelon (platoon, company, battalion, regiment, division)
  callsign?: string;    // Radio callsign (e.g., "ALPHA", "BRAVO", "1-1")
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

// Report Types - Standardized military report formats
export type ReportFormat = 'sitrep' | 'intsumm' | 'opsumm' | 'logsitrep' | 'salute';

// SALUTE Report (Size, Activity, Location, Unit, Time, Equipment)
export interface SALUTEReport {
  report_id: string;
  turn: number;
  timestamp: string;
  size: string;        // 兵力規模 (e.g., "大隊", "連隊", "1個小隊")
  activity: string;    // 活動内容 (e.g., "移動中", "防御配置", "攻撃準備")
  location: string;    // 位置 (grid reference or area name)
  unit: string;        // 所属部隊
  time: string;        // 時刻
  equipment: string;   // 装備・状態 (e.g., "戦車5両", "小火器のみ")
  assessment?: string; // 評価・脅威度
}

// INTSUM (Intelligence Summary)
export interface INTSUMReport {
  report_id: string;
  turn: number;
  timestamp: string;
  period: string;       // 対象期間
  summary: string;     // 要約
  enemy_dispositions: Array<{
    unit_name: string;
    position: string;
    strength: string;
    assessment: string; // confirmed, estimated, unknown
  }>;
  friendly_dispositions: Array<{
    unit_name: string;
    position: string;
    status: string;
  }>;
  intelligence_gaps: string[];  // 未確認情報
  recommendations: string[];
}

// OPSUM (Operations Summary)
export interface OPSUMReport {
  report_id: string;
  turn: number;
  timestamp: string;
  period: string;
  operations_conducted: Array<{
    operation_name: string;
    objective: string;
    outcome: 'success' | 'partial' | 'failed' | 'pending';
    units_involved: string[];
    results: string;
  }>;
  current_operations: Array<{
    operation_name: string;
    status: 'ongoing' | 'paused' | 'completed';
    units_involved: string[];
  }>;
  planned_operations: Array<{
    operation_name: string;
    objective: string;
    planned_time: string;
    units_assigned: string[];
  }>;
  commander_assessment: string;
}

// LOGSITREP (Logistical Situation Report)
export interface LOGSITREPReport {
  report_id: string;
  turn: number;
  timestamp: string;
  period: string;
  supply_status: {
    ammo: { full: number; depleted: number; exhausted: number };
    fuel: { full: number; depleted: number; exhausted: number };
    readiness: { full: number; depleted: number; exhausted: number };
  };
  supply_lines: Array<{
    line_id: string;
    status: 'open' | 'threatened' | 'cut';
    last_verified: string;
  }>;
  attrition: Array<{
    unit: string;
    ammo_spent: number;
    fuel_spent: number;
    maintenance_needed: boolean;
  }>;
  resupply_requests: Array<{
    unit: string;
    type: 'ammo' | 'fuel' | 'maintenance';
    priority: 'high' | 'normal' | 'low';
    status: 'pending' | 'approved' | 'delivered';
  }>;
}

// Unified Report Response
export interface UnifiedReport {
  report_id: string;
  format: ReportFormat;
  turn: number;
  timestamp: string;
  generated_at: string;
  content: Sitrep | INTSUMReport | OPSUMReport | LOGSITREPReport | SALUTEReport;
}

// Report Generation Request
export interface ReportGenerationRequest {
  game_id: number;
  format: ReportFormat;
  turn?: number;  // If not specified, current turn
  options?: {
    include_map?: boolean;
    include_history?: boolean;
    period?: string;
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

// ============================================================
// CPX-3: MGRS/APP-6 Types
// ============================================================

// MGRS Grid Coordinate
export interface MGRSCoordinate {
  grid_square: string;  // e.g., "34S"
  easting: number;      // meters (0-999999)
  northing: number;     // meters (0-999999)
  precision: '1m' | '10m' | '100m' | '1km' | '10km' | '100km';
}

export interface GridPosition {
  x: number;           // internal XY coordinate (0-based)
  y: number;           // internal XY coordinate (0-based)
  mgrs?: MGRSCoordinate; // optional MGRS representation
}

// Phase Line - control measure
export interface PhaseLine {
  id: string;
  name: string;
  points: GridPosition[];
  color: string;
  line_style: 'solid' | 'dashed' | 'dotted';
  status: 'reported' | 'contact' | 'lost';
}

// Boundary - control measure
export interface Boundary {
  id: string;
  name: string;
  owning_side: 'player' | 'enemy' | 'neutral';
  points: GridPosition[];
  color: string;
  line_style: 'solid' | 'dashed';
}

// Airspace - control measure
export interface Airspace {
  id: string;
  name: string;
  type: 'air_corridor' | 'restricted' | 'ada_zone' | 'no_fly';
  points: GridPosition[];
  altitude_low?: number;  // feet AGL
  altitude_high?: number; // feet AGL
  color: string;
  status: 'active' | 'inactive';
}

// APP-6 Unit Symbol Configuration
export interface APP6SymbolConfig {
  symbol: string;           // APP-6 symbol code (e.g., "S-", "G-", "X-")
  affiliation: 'friend' | 'enemy' | 'neutral' | 'unknown';
  status: 'present' | 'anticipated' | 'suspect' | 'reimbursed';
  echelon: string;          // unit echelon (platoon, company, battalion, etc.)
  modifier: string;         // additional modifiers (task force, reinforced, etc.)
}

// Unit with APP-6 symbol support
export interface UnitWithAPP6 extends Unit {
  app6_symbol?: APP6SymbolConfig;
  grid_position?: GridPosition;
}

// Control Measures for game state
export interface ControlMeasures {
  phase_lines: PhaseLine[];
  boundaries: Boundary[];
  airspaces: Airspace[];
}

// Game State extended with control measures
export interface GameStateWithControlMeasures extends GameState {
  grid_system: 'XY' | 'MGRS';
  control_measures?: ControlMeasures;
}

// RBAC Types
export type UserRole = 'blue' | 'red' | 'white' | 'observer' | 'admin';

export interface User {
  id: number;
  username: string;
  role: UserRole;
  game_id?: number;
  created_at: string;
}

export interface UserWithGame extends User {
  game_name?: string;
}

// WebSocket Notification Types
export type NotificationType = 'turn_advance' | 'order_received' | 'sitrep_ready' | 'game_update' | 'chat_message';

export interface WebSocketMessage {
  type: NotificationType;
  game_id: number;
  turn?: number;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface NotificationPayload {
  message: string;
  game_id: number;
  turn?: number;
  type: NotificationType;
}

// CCIR/PIR/ROE Types - Command and Control prerequisites
export type CCIRCategory = 'isr' | 'fires' | 'sustainment' | 'c2';

export interface CCIRItem {
  id: string;
  category: CCIRCategory;
  description: string;
  required: boolean;
  satisfied: boolean;
  satisfied_turn?: number;
}

export interface PIRItem {
  id: string;
  description: string;
  priority: number;
  intel_type: 'enemy_location' | 'enemy_intent' | 'terrain' | 'weather' | 'other';
  satisfied: boolean;
  intelligence_source?: string;
}

export interface ROERule {
  id: string;
  type: 'attack_restriction' | 'fire_support' | 'airspace' | 'civilian_protection';
  description: string;
  applies_to: ('player' | 'enemy' | 'both')[];
  active: boolean;
}

export interface CCIRChecklist {
  isr: CCIRItem[];
  fires: CCIRItem[];
  sustainment: CCIRItem[];
  c2: CCIRItem[];
}

export interface CCIREvaluation {
  overall_compliance: number;
  category_results: {
    isr: { passed: number; total: number };
    fires: { passed: number; total: number };
    sustainment: { passed: number; total: number };
    c2: { passed: number; total: number };
  };
  combat_modifier: number;
  failed_checks: string[];
}

// OPORD/FRAGO Types - SMESC Format (Situation, Mission, Execution, Coordination, Service Support)

export interface OpordSituation {
  enemy_situation: string;        // 敵の現状
  friendly_situation: string;     // 味方の現状
  terrain_impact: string;         // 地形の影響
  weather_impact: string;         // 天候の影響
  attachments?: string[];         // 追加兵力
  detachments?: string[];        // 除外兵力
}

export interface OpordMission {
  task: string;                   // 任務（動詞+対象+目的）
  purpose: string;               // 任務の目的
  end_state: string;              // 終結状態
  success_criteria: string[];     // 成功基準
}

export interface OpordExecution {
  concept_of_operations: string; // 作戦構想
  phase_timeline: string[];      // 段階的展開
  tasks_by_unit: Array<{
    unit: string;
    task: string;
    timing?: string;
  }>;
  coordination: string;           // 調整事項
  contingencies: Array<{
    condition: string;
    action: string;
  }>;
  command_signal: string;         // 指揮系統・通信
}

export interface OpordCoordination {
  boundaries: Array<{
    name: string;
    line: string;
    control: string;
  }>;
  phase_lines: Array<{
    name: string;
    location: string;
    criteria: string;
  }>;
  fire_support: string;           // 火力支援調整
  air_support: string;            // 航空支援
  engineer_support: string;       // 工兵支援
  c2_relationships: string;      // 指揮系統
}

export interface OpordServiceSupport {
  supply: {
    ammo: string;                // 弾薬補給
    fuel: string;                // 燃料補給
    other: string;               // 各種補給
  };
  maintenance: string;           // 整備
  medical: string;               // 衛生
  transportation: string;        // 輸送
  evacuation: string;            // 後送
  field_services: string;        // 野外サービス
  general_supply: string;        // 一般補給
}

export interface OPORD {
  opord_id: string;
  game_id: number;
  title: string;
  classification: 'unclassified' | 'confidential' | 'secret' | 'top_secret';
  effective_date: string;
  // SMESC Sections
  situation: OpordSituation;
  mission: OpordMission;
  execution: OpordExecution;
  coordination: OpordCoordination;
  service_support: OpordServiceSupport;
  // Metadata
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface OpordUpdateRequest {
  opord_id?: string;
  game_id: number;
  title?: string;
  classification?: 'unclassified' | 'confidential' | 'secret' | 'top_secret';
  effective_date?: string;
  situation?: Partial<OpordSituation>;
  mission?: Partial<OpordMission>;
  execution?: Partial<OpordExecution>;
  coordination?: Partial<OpordCoordination>;
  service_support?: Partial<OpordServiceSupport>;
}

export interface OpordResponse {
  success: boolean;
  opord?: OPORD;
  error?: string;
}

// ============================================================
// CPX-4: MEL/MIL (Inject) System Types
// ============================================================

// Inject Types - Categories of injects
export type InjectType =
  | 'communications_outage'
  | 'ew_interference'
  | 'supply_interdiction'
  | 'weather_deterioration'
  | 'reinforcements'
  | 'air_strike_alert'
  | 'civilian_refugees'
  | 'equipment_malfunction'
  | 'intelligence_report'
  | 'command_decision';

// Inject Status - Current state
export type InjectStatus = 'available' | 'triggered' | 'expired' | 'cancelled';

// Inject Timing - When to trigger
export type InjectTiming = 'immediate' | 'conditional' | 'scheduled';

// Inject Condition - Trigger conditions
export interface InjectCondition {
  type: 'turn_number' | 'unit_position' | 'unit_status' | 'game_state' | 'random';
  params: Record<string, unknown>;
}

// Inject Effect - What the inject modifies
export interface InjectEffect {
  target: 'movement' | 'combat' | 'reconnaissance' | 'supply' | 'morale' | 'game_state';
  modifier: number;
  duration_turns?: number;
  description: string;
}

// Inject Observation - What to observe/evaluate
export interface InjectObservation {
  item: string;
  expected_response: string;
  evaluation_criteria: string;
}

// Main Inject Definition
export interface Inject {
  id: string;
  name: string;
  description: string;
  type: InjectType;
  timing: InjectTiming;
  status: InjectStatus;
  conditions: InjectCondition[];
  effects: InjectEffect[];
  observations: InjectObservation[];
  evaluation_points: number;
  difficulty: 'easy' | 'medium' | 'hard';
  triggered_turn?: number;
  created_at?: string;
}

// Inject Log - Audit trail
export interface InjectLog {
  id: string;
  inject_id: string;
  game_id: number;
  turn: number;
  timestamp: string;
  trigger_type: 'immediate' | 'condition_met' | 'scheduled';
  effects_applied: Record<string, unknown>[];
  results: Record<string, unknown>;
}

// ==========================================
// Logistics Types (CPX-7)
// ==========================================

// Supply class types (NATO standard)
export type SupplyClass = 'class_i' | 'class_iii' | 'class_v' | 'class_vi' | 'class_vii' | 'class_ix';

// Mode of Transport
export type TransportMode = 'road' | 'rail' | 'air' | 'sea' | 'pipeline';

// Supply route status
export type SupplyRouteStatus = 'open' | 'interdicted' | 'cut' | 'unknown';

// Supply node type
export type SupplyNodeType = 'depot' | 'forward_operating_base' | 'railhead' | 'seaport' | 'airfield';

// Logistics status for reporting
export type LogisticsStatus = 'adequate' | 'marginal' | 'critical' | 'unknown';

// Supply node (fixed location)
export interface SupplyNode {
  id: string;
  name: string;
  node_type: SupplyNodeType;
  x: number;
  y: number;
  side: 'player' | 'enemy';
  // Inventory (supply points)
  class_i_points: number;  // Rations
  class_iii_points: number; // Fuel
  class_v_points: number;  // Ammo
  class_vi_points: number; // Personal items
  class_vii_points: number; // Major end items
  class_ix_points: number; // Repair parts
  capacity: number;
  current_capacity: number;
  // Status
  status: 'operational' | 'damaged' | 'destroyed';
  last_resupply_turn: number;
  next_resupply_turn: number;
}

// Supply route between nodes
export interface SupplyRoute {
  id: string;
  name: string;
  source_node_id: string;
  destination_node_id: string;
  transport_mode: TransportMode;
  distance: number;  // in km
  status: SupplyRouteStatus;
  interdiction_level: number;  // 0-100, probability of delay/interdiction
  travel_time_hours: number;
  last_verified_turn: number;
}

// Convoy / transport unit
export interface Convoy {
  id: string;
  name: string;
  origin_node_id: string;
  destination_node_id: string;
  current_x: number;
  current_y: number;
  transport_mode: TransportMode;
  // Cargo
  class_i_points: number;
  class_iii_points: number;
  class_v_points: number;
  class_vi_points: number;
  class_ix_points: number;
  // Status
  status: 'moving' | 'loading' | 'unloading' | 'waiting' | 'destroyed';
  departure_turn: number;
  estimated_arrival_turn: number;
  actual_arrival_turn?: number;
  route_id: string;
}

// Logistics status for a unit
export interface UnitLogisticsStatus {
  unit_id: number;
  supply_level: LogisticsStatus;
  last_resupply_turn: number;
  next_scheduled_resupply: number;
  nearest_node_id?: string;
  nearest_node_distance?: number;
  is_on_supply_route: boolean;
  connected_to_network: boolean;
}

// Logistics summary for LOGSITREP
export interface LogisticsSummary {
  turn: number;
  total_class_i: number;
  total_class_iii: number;
  total_class_v: number;
  class_iii_status: LogisticsStatus;
  class_v_status: LogisticsStatus;
  active_convoys: number;
  routes_open: number;
  routes_interdicted: number;
  routes_cut: number;
  nodes_operational: number;
  nodes_damaged: number;
  nodes_destroyed: number;
  critical_shortages: string[];
}

// Resupply order
export interface ResupplyOrder {
  unit_id: number;
  priority: 'critical' | 'normal' | 'low';
  supply_classes: SupplyClass[];
  requested_amount: number;
  requested_turn: number;
  status: 'pending' | 'assigned' | 'in_transit' | 'delivered' | 'cancelled';
  assigned_convoy_id?: string;
}
