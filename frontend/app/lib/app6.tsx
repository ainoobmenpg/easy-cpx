// APP-6 Symbol Utility Functions
// Provides symbol generation and color configuration for APP-6 compliant unit markers

import { memo } from 'react';
import type { Unit, APP6SymbolConfig } from '@shared/types';

// APP-6 symbol codes for ground units
const APP6_SYMBOL_CODES: Record<string, string> = {
  infantry: 'S-',
  armor: 'G-',
  artillery: 'F-',
  air_defense: 'A-',
  recon: 'R-',
  uav: 'Z-',
  support: 'S--P',
  hq: 'E-',
  atgm: 'S--AT',
};

// Affiliation mappings
const AFFILIATION_MAP: Record<string, string> = {
  player: 'friend',
  enemy: 'enemy',
  neutral: 'neutral',
};

// Status mappings
const STATUS_MAP: Record<string, string> = {
  intact: 'present',
  light_damage: 'present',
  medium_damage: 'present',
  heavy_damage: 'anticipated',
  destroyed: 'reimbursed',
};

// Standard APP-6 colors
export const APP6_COLORS = {
  friend: '#3b82f6',    // Blue
  enemy: '#ef4444',      // Red
  neutral: '#22c55e',   // Green
  unknown: '#a855f7',   // Purple
  // Frame colors
  friend_frame: '#1d4ed8',
  enemy_frame: '#b91c1c',
  neutral_frame: '#15803d',
  unknown_frame: '#7c3aed',
};

// Get APP-6 symbol code for unit type
export function getApp6SymbolCode(unitType: string): string {
  return APP6_SYMBOL_CODES[unitType] || 'S-';
}

// Get affiliation from side
export function getAffiliation(side: string): 'friend' | 'enemy' | 'neutral' | 'unknown' {
  return (AFFILIATION_MAP[side] || 'unknown') as 'friend' | 'enemy' | 'neutral' | 'unknown';
}

// Get status from unit status
export function getStatus(unitStatus: string): 'present' | 'anticipated' | 'suspect' | 'reimbursed' {
  return (STATUS_MAP[unitStatus] || 'present') as 'present' | 'anticipated' | 'suspect' | 'reimbursed';
}

// Get color for affiliation
export function getColorForAffiliation(affiliation: string): string {
  return APP6_COLORS[affiliation as keyof typeof APP6_COLORS] || '#ffffff';
}

// Generate APP-6 symbol configuration for a unit
export function getApp6Config(unit: Unit): APP6SymbolConfig {
  return {
    symbol: getApp6SymbolCode(unit.type),
    affiliation: getAffiliation(unit.side),
    status: getStatus(unit.status),
    echelon: 'C',  // Default to company
    modifier: '',
  };
}

// Convert unit to APP-6 SVG path
// Returns the SVG path for the APP-6 symbol based on type
export function getApp6SvgPath(unitType: string, affiliation: string): string {
  const baseSize = 1.0;

  // Common APP-6 symbol shapes (simplified)
  const paths: Record<string, string> = {
    // Infantry - X shape
    infantry: `M -${baseSize * 0.4} -${baseSize * 0.4} L ${baseSize * 0.4} ${baseSize * 0.4} M -${baseSize * 0.4} ${baseSize * 0.4} L ${baseSize * 0.4} -${baseSize * 0.4}`,
    // Armor - Arrow right
    armor: `M -${baseSize * 0.3} -${baseSize * 0.4} L ${baseSize * 0.5} 0 L -${baseSize * 0.3} ${baseSize * 0.4}`,
    // Artillery - Plus
    artillery: `M 0 -${baseSize * 0.4} L 0 ${baseSize * 0.4} M -${baseSize * 0.4} 0 L ${baseSize * 0.4} 0`,
    // Recon - Diamond
    recon: `M 0 -${baseSize * 0.5} L ${baseSize * 0.4} 0 L 0 ${baseSize * 0.5} L -${baseSize * 0.4} 0 Z`,
    // Air Defense - Triangle up
    air_defense: `M 0 -${baseSize * 0.5} L ${baseSize * 0.5} ${baseSize * 0.4} L -${baseSize * 0.5} ${baseSize * 0.4} Z`,
    // UAV - Diamond with dot
    uav: `M 0 -${baseSize * 0.5} L ${baseSize * 0.4} 0 L 0 ${baseSize * 0.5} L -${baseSize * 0.4} 0 Z M 0 0 A 0.1 0.1 0 1 1 0.001 0`,
    // Support - Rectangle
    support: `M -${baseSize * 0.3} -${baseSize * 0.3} L ${baseSize * 0.3} -${baseSize * 0.3} L ${baseSize * 0.3} ${baseSize * 0.3} L -${baseSize * 0.3} ${baseSize * 0.3} Z`,
    // HQ - Star
    hq: `M 0 -${baseSize * 0.5} L ${baseSize * 0.15} -${baseSize * 0.15} L ${baseSize * 0.5} -${baseSize * 0.15} L ${baseSize * 0.25} ${baseSize * 0.1} L ${baseSize * 0.35} ${baseSize * 0.5} L 0 ${baseSize * 0.3} L -${baseSize * 0.35} ${baseSize * 0.5} L -${baseSize * 0.25} ${baseSize * 0.1} L -${baseSize * 0.5} -${baseSize * 0.15} L -${baseSize * 0.15} -${baseSize * 0.15} Z`,
    // Default
    default: `M 0 -${baseSize * 0.4} L ${baseSize * 0.4} 0 L 0 ${baseSize * 0.4} L -${baseSize * 0.4} 0 Z`,
  };

  return paths[unitType] || paths.default;
}

// Get dash array for line style
export function getDashArray(lineStyle: 'solid' | 'dashed' | 'dotted'): string {
  switch (lineStyle) {
    case 'dashed':
      return '0.3,0.2';
    case 'dotted':
      return '0.1,0.1';
    default:
      return '';
  }
}

// Format MGRS grid reference
export function formatMGRS(x: number, y: number, precision: '1km' | '10km' | '100km' = '1km'): string {
  // Simplified MGRS format for internal coordinates
  // In real implementation, would use proper UTM conversion
  const gridZone = '34S';
  const easting = Math.floor(x / 10) % 100;
  const northing = Math.floor(y / 10) % 100;

  if (precision === '100km') {
    return gridZone;
  } else if (precision === '10km') {
    return `${gridZone} ${String.fromCharCode(65 + easting % 20)}${String.fromCharCode(65 + northing % 20)}`;
  } else {
    const eastingStr = String(x).padStart(3, '0').slice(-3);
    const northingStr = String(y).padStart(3, '0').slice(-3);
    return `${gridZone} ${eastingStr} ${northingStr}`;
  }
}

// ============================================================
// Control Measures Overlay Types
// ============================================================

export interface ControlMeasurePoint {
  x: number;
  y: number;
}

export interface PhaseLine {
  id: string;
  name: string;
  points: ControlMeasurePoint[];
  color: string;
  lineStyle: 'solid' | 'dashed' | 'dotted';
  status: 'reported' | 'contact' | 'lost';
}

export interface Boundary {
  id: string;
  name: string;
  owningSide: 'player' | 'enemy' | 'neutral';
  points: ControlMeasurePoint[];
  color: string;
  lineStyle: 'solid' | 'dashed';
}

export interface Airspace {
  id: string;
  name: string;
  type: 'air_corridor' | 'restricted' | 'ada_zone' | 'no_fly';
  points: ControlMeasurePoint[];
  altitudeLow?: number;
  altitudeHigh?: number;
  color: string;
  status: 'active' | 'inactive';
}

// Control measure colors
export const CONTROL_MEASURE_COLORS = {
  phaseLine: {
    reported: '#22c55e', // Green
    contact: '#f59e0b',  // Amber
    lost: '#ef4444',     // Red
  },
  boundary: {
    player: '#3b82f6',   // Blue
    enemy: '#ef4444',     // Red
    neutral: '#22c55e',  // Green
  },
  airspace: {
    air_corridor: '#06b6d4',  // Cyan
    restricted: '#f59e0b',     // Amber
    ada_zone: '#ef4444',       // Red
    no_fly: '#8b5cf6',        // Purple
  },
};

// Generate SVG path for phase line
export function getPhaseLinePath(points: ControlMeasurePoint[]): string {
  if (points.length < 2) return '';
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    path += ` L ${points[i].x} ${points[i].y}`;
  }
  return path;
}

// Generate SVG path for boundary (closed polygon)
export function getBoundaryPath(points: ControlMeasurePoint[]): string {
  if (points.length < 2) return '';
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    path += ` L ${points[i].x} ${points[i].y}`;
  }
  path += ' Z'; // Close the polygon
  return path;
}

// Generate SVG path for airspace (rectangle or polygon)
export function getAirspacePath(points: ControlMeasurePoint[]): string {
  if (points.length < 2) return '';
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    path += ` L ${points[i].x} ${points[i].y}`;
  }
  path += ' Z';
  return path;
}

// Get dash array for control measure line style
export function getControlMeasureDashArray(lineStyle: 'solid' | 'dashed' | 'dotted'): string {
  switch (lineStyle) {
    case 'dashed':
      return '0.3,0.2';
    case 'dotted':
      return '0.1,0.1';
    default:
      return '';
  }
}

// Generate legend items for control measures
export function getControlMeasureLegend(): { label: string; color: string; type: string }[] {
  return [
    { label: 'Phase Line (Reported)', color: CONTROL_MEASURE_COLORS.phaseLine.reported, type: 'phase' },
    { label: 'Phase Line (Contact)', color: CONTROL_MEASURE_COLORS.phaseLine.contact, type: 'phase' },
    { label: 'Phase Line (Lost)', color: CONTROL_MEASURE_COLORS.phaseLine.lost, type: 'phase' },
    { label: 'Boundary (Friendly)', color: CONTROL_MEASURE_COLORS.boundary.player, type: 'boundary' },
    { label: 'Boundary (Enemy)', color: CONTROL_MEASURE_COLORS.boundary.enemy, type: 'boundary' },
    { label: 'Air Corridor', color: CONTROL_MEASURE_COLORS.airspace.air_corridor, type: 'airspace' },
    { label: 'Restricted Area', color: CONTROL_MEASURE_COLORS.airspace.restricted, type: 'airspace' },
    { label: 'ADA Zone', color: CONTROL_MEASURE_COLORS.airspace.ada_zone, type: 'airspace' },
    { label: 'No-Fly Zone', color: CONTROL_MEASURE_COLORS.airspace.no_fly, type: 'airspace' },
  ];
}

// ============================================================
// UnitMarker Component - APP-6 Compliant Unit Display
// ============================================================

interface UnitMarkerProps {
  unit: Unit;
  selectedUnitId: number | null;
  onSelect: (unit: Unit) => void;
  showExactPosition?: boolean;
}

// Memoized Unit component for performance
// FoW display: show exact position marker and UI position marker separately
export const UnitMarker = memo(function UnitMarker({
  unit,
  selectedUnitId,
  onSelect,
  showExactPosition = false
}: UnitMarkerProps) {
  // FoW: Determine displayed position based on observation confidence
  const isEnemy = unit.side === 'enemy';
  const confidence = unit.observation_confidence;
  const hasEstimatedPosition = isEnemy && (confidence === 'unknown' || confidence === 'estimated') &&
    unit.estimated_x !== undefined && unit.estimated_y !== undefined;

  // UI display position (what player sees)
  const displayX = hasEstimatedPosition ? unit.estimated_x! : unit.x;
  const displayY = hasEstimatedPosition ? unit.estimated_y! : unit.y;

  // Exact position (true position - for internal use)
  const exactX = unit.x;
  const exactY = unit.y;

  const svgX = Math.floor(displayX) + 0.5;
  const svgY = Math.floor(displayY) + 0.5;
  const exactSvgX = Math.floor(exactX) + 0.5;
  const exactSvgY = Math.floor(exactY) + 0.5;

  // APP-6 affiliation color
  const affiliation = getAffiliation(unit.side);
  const sideColor = getColorForAffiliation(affiliation);
  const frameColor = affiliation === 'friend' ? APP6_COLORS.friend_frame :
                     affiliation === 'enemy' ? APP6_COLORS.enemy_frame :
                     affiliation === 'neutral' ? APP6_COLORS.neutral_frame :
                     APP6_COLORS.unknown_frame;

  const isSelected = selectedUnitId === unit.id;

  // APP-6 symbol code
  const app6Code = getApp6SymbolCode(unit.type);
  const app6Path = getApp6SvgPath(unit.type, affiliation);

  // Status color - APP-6 style
  const statusColors: Record<string, string> = {
    intact: '#22c55e',      // Green - full strength
    light_damage: '#eab308', // Yellow - light damage
    medium_damage: '#f97316', // Orange - medium damage
    heavy_damage: '#ef4444', // Red - heavy damage
    destroyed: '#6b7280'    // Gray - destroyed
  };
  const statusColor = statusColors[unit.status] || '#22c55e';

  // Observation confidence styling for enemy units - FoW display
  const confidenceScore = unit.confidence_score;
  let confidenceOpacity = 1.0;
  let confidenceBorder = false;
  let confidenceLabel = '';
  let isEstimatedMarker = false;

  if (isEnemy && confidence) {
    if (confidence === 'unknown') {
      confidenceOpacity = 0.5;
      confidenceBorder = true;
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : '?';
      isEstimatedMarker = hasEstimatedPosition;
    } else if (confidence === 'estimated') {
      confidenceOpacity = 0.75;
      confidenceBorder = true;
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : '~';
      isEstimatedMarker = hasEstimatedPosition;
    } else {
      confidenceLabel = confidenceScore !== undefined ? `${confidenceScore}%` : 'OK';
    }
  }

  // Echelon indicator (simplified)
  const echelonChar = unit.echelon ? unit.echelon.charAt(0).toUpperCase() : 'C';

  return (
    <g onClick={() => onSelect(unit)} style={{ cursor: 'pointer' }}>
      {/* Exact position marker - shown when showExactPosition is true (for internal/debug view) */}
      {showExactPosition && isEnemy && (
        <g>
          <circle cx={exactSvgX} cy={exactSvgY} r="0.5" fill="none" stroke="#ff00ff" strokeWidth="0.15" strokeDasharray="0.15,0.1" opacity={0.8} />
          <text x={exactSvgX - 0.8} y={exactSvgY - 0.6} fontSize="0.35" fill="#ff00ff" fontWeight="bold" opacity={0.9}>
            True
          </text>
        </g>
      )}
      {/* FoW estimated position marker - dashed circle */}
      {isEstimatedMarker && (
        <circle cx={svgX} cy={svgY} r="0.7" fill="none" stroke="#fbbf24" strokeWidth="0.1" strokeDasharray="0.2,0.1" opacity={confidenceOpacity * 0.7} />
      )}
      {/* APP-6 Symbol Frame - affiliation color */}
      <rect x={svgX - 0.6} y={svgY - 0.5} width="1.2" height="1.0"
        fill={sideColor} stroke={isSelected ? '#fff' : (confidenceBorder ? '#fbbf24' : frameColor)}
        strokeWidth={isSelected ? 0.15 : 0.08} opacity={confidenceOpacity * 0.95} rx="0.1" />
      {/* APP-6 Symbol - unit type graphic */}
      <path d={app6Path} stroke="#fff" strokeWidth="0.12" fill="none" opacity={confidenceOpacity}
        transform={`translate(${svgX}, ${svgY}) scale(0.8)`} />
      {/* Echelon indicator */}
      <text x={svgX - 0.4} y={svgY - 0.35} fontSize="0.35" fill="#fff" fontWeight="bold" opacity={confidenceOpacity}>
        {echelonChar}
      </text>
      {/* Unit name with confidence label */}
      <text x={svgX + 0.8} y={svgY + 0.8} fontSize="0.5" fill="#fff" stroke="#000" strokeWidth="0.15" paintOrder="stroke" fontWeight="bold" opacity={confidenceOpacity}>
        {unit.name}{confidenceLabel ? ` (${confidenceLabel})` : ''}
      </text>
      {/* Status indicator box */}
      <rect x={svgX + 0.4} y={svgY + 0.4} width="0.3" height="0.2" fill={statusColor} stroke="#000" strokeWidth="0.05" opacity={confidenceOpacity} rx="0.05" />
    </g>
  );
});
