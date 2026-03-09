// APP-6 Symbol Utility Functions
// Provides symbol generation and color configuration for APP-6 compliant unit markers

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
export function getAffiliation(side: string): string {
  return AFFILIATION_MAP[side] || 'unknown';
}

// Get status from unit status
export function getStatus(unitStatus: string): string {
  return STATUS_MAP[unitStatus] || 'present';
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
