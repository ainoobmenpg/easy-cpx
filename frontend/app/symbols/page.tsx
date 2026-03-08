'use client';

import { useState } from 'react';

interface SymbolInfo {
  id: string;
  name: string;
  nameJa: string;
  description: string;
  path: string;
  category: string;
}

const natoSymbols: SymbolInfo[] = [
  // Movement & Maneuver
  {
    id: 'infantry',
    name: 'Infantry',
    nameJa: '歩兵',
    description: 'Crossed lines (saltire) representing infantry',
    path: 'M25 25 L75 75 M75 25 L25 75',
    category: 'Movement & Maneuver'
  },
  {
    id: 'armor',
    name: 'Armored',
    nameJa: '装甲',
    description: 'Double arrow pointing outward',
    path: 'M30 50 L50 30 L50 40 L70 40 L70 60 L50 60 L50 70 Z M70 50 L50 30 L50 40 L30 40 L30 60 L50 60 L50 70 Z',
    category: 'Movement & Maneuver'
  },
  {
    id: 'tank',
    name: 'Tank',
    nameJa: '戦車',
    description: 'Single arrow pointing in direction of movement',
    path: 'M50 25 L70 50 L50 40 L30 50 Z',
    category: 'Movement & Maneuver'
  },
  {
    id: 'mechanized_infantry',
    name: 'Mechanized Infantry',
    nameJa: '機械化歩兵',
    description: 'Infantry symbol with armored frame',
    path: 'M25 30 L75 70 M75 30 L25 70 M30 25 L70 25 M30 75 L70 75',
    category: 'Movement & Maneuver'
  },
  {
    id: 'cavalry',
    name: 'Cavalry',
    nameJa: '騎兵',
    description: 'Horizontal lines',
    path: 'M20 40 L80 40 M20 50 L80 50 M20 60 L80 60',
    category: 'Movement & Maneuver'
  },
  {
    id: 'combined_arms',
    name: 'Combined Arms',
    nameJa: '統合機動',
    description: 'Square in rectangle',
    path: 'M30 35 L70 35 L70 65 L30 65 Z',
    category: 'Movement & Maneuver'
  },
  // Fires
  {
    id: 'artillery',
    name: 'Artillery',
    nameJa: '砲兵',
    description: 'Plus sign (+) for indirect fire',
    path: 'M50 25 L50 75 M25 50 L75 50',
    category: 'Fires'
  },
  {
    id: 'mortar',
    name: 'Mortar',
    nameJa: '迫撃砲',
    description: 'Small cross in circle',
    path: 'M50 35 L50 65 M35 50 L65 50 M50 20 A30 30 0 1 0 50 80 A30 30 0 1 0 50 20',
    category: 'Fires'
  },
  {
    id: 'anti_tank',
    name: 'Anti-Tank',
    nameJa: '対戦車',
    description: 'Arrow with cross',
    path: 'M50 25 L65 50 L50 45 L35 50 Z M30 35 L70 70 M70 35 L30 70',
    category: 'Fires'
  },
  // Intelligence & Reconnaissance
  {
    id: 'reconnaissance',
    name: 'Reconnaissance',
    nameJa: '偵察',
    description: 'Diamond/rhombus shape',
    path: 'M50 25 L75 50 L50 75 L25 50 Z',
    category: 'Intelligence'
  },
  {
    id: 'observation_post',
    name: 'Observation Post',
    nameJa: '監視所',
    description: 'Small diamond with line',
    path: 'M50 35 L65 50 L50 65 L35 50 Z M50 25 L50 35',
    category: 'Intelligence'
  },
  // Protection
  {
    id: 'air_defense',
    name: 'Air Defense',
    nameJa: '防空',
    description: 'Missile shape with launcher',
    path: 'M50 30 L60 55 L50 48 L40 55 Z M50 30 L50 20 M35 60 L65 60',
    category: 'Protection'
  },
  {
    id: 'engineer',
    name: 'Engineer',
    nameJa: '工兵',
    description: 'Bridge/arch symbol',
    path: 'M25 40 L25 60 L75 60 L75 40 M30 40 L30 30 M70 40 L70 30 M30 30 L70 30',
    category: 'Protection'
  },
  // C2 & Support
  {
    id: 'headquarters',
    name: 'Headquarters',
    nameJa: '司令部',
    description: 'Flag symbol',
    path: 'M30 25 L30 75 L70 50 Z M30 25 L30 20',
    category: 'Command & Control'
  },
  {
    id: 'signal',
    name: 'Signal/Comm',
    nameJa: '通信',
    description: 'Antenna/radio waves',
    path: 'M50 25 L50 55 M35 45 L65 45 M25 55 L40 40 M75 55 L60 40',
    category: 'Support'
  },
  {
    id: 'logistics',
    name: 'Logistics',
    nameJa: '後方',
    description: 'Box with X',
    path: 'M25 30 L75 30 L75 70 L25 70 Z M35 40 L65 60 M65 40 L35 60',
    category: 'Support'
  },
  {
    id: 'medical',
    name: 'Medical',
    nameJa: '衛生',
    description: 'Red crystal (medical facility)',
    path: 'M50 25 L65 40 L50 75 L35 40 Z',
    category: 'Support'
  },
  // Equipment
  {
    id: 'apc',
    name: 'APC',
    nameJa: '装甲兵員輸送車',
    description: 'Armored personnel carrier',
    path: 'M30 35 L70 35 L70 65 L30 65 Z M35 40 L35 45 M65 40 L65 45',
    category: 'Equipment'
  },
  {
    id: 'ifv',
    name: 'IFV',
    nameJa: '歩兵戦闘車',
    description: 'Infantry fighting vehicle',
    path: 'M30 35 L70 35 L70 65 L30 65 Z M40 40 L60 40 M40 60 L60 60 M50 40 L50 60',
    category: 'Equipment'
  },
  {
    id: 'supply_truck',
    name: 'Supply Truck',
    nameJa: '補給トラック',
    description: 'Truck with cargo',
    path: 'M25 35 L55 35 L55 65 L25 65 Z M55 45 L75 45 L75 65 L55 65 M30 40 L50 40',
    category: 'Equipment'
  },
];

export default function SymbolsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSide, setSelectedSide] = useState<'friend' | 'enemy' | 'neutral' | 'unknown'>('friend');

  const categories = ['all', ...new Set(natoSymbols.map(s => s.category))];

  const filteredSymbols = selectedCategory === 'all'
    ? natoSymbols
    : natoSymbols.filter(s => s.category === selectedCategory);

  const sideColors = {
    friend: '#2196F3',  // Blue
    enemy: '#F44336',  // Red
    neutral: '#4CAF50', // Green
    unknown: '#9E9E9E'  // Gray
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-blue-400 mb-2">NATO APP-6 Military Symbols</h1>
        <p className="text-gray-400">Debug page for NATO military symbology</p>
      </header>

      {/* Controls */}
      <div className="flex gap-6 mb-8 flex-wrap">
        <div>
          <label className="block text-sm text-gray-400 mb-2">Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">Side/Affiliation</label>
          <div className="flex gap-2">
            {(['friend', 'enemy', 'neutral', 'unknown'] as const).map(side => (
              <button
                key={side}
                onClick={() => setSelectedSide(side)}
                className={`px-3 py-2 rounded border ${
                  selectedSide === side
                    ? 'border-white bg-gray-700'
                    : 'border-gray-700 bg-gray-800'
                }`}
                style={{
                  borderColor: selectedSide === side ? sideColors[side] : undefined
                }}
              >
                <span
                  className="inline-block w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: sideColors[side] }}
                />
                {side === 'friend' ? '友軍' : side === 'enemy' ? '敵' : side === 'neutral' ? '中立' : '不明'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Symbol Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {filteredSymbols.map((symbol) => (
          <div
            key={symbol.id}
            className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-500"
          >
            {/* Symbol Display */}
            <div className="aspect-square bg-gray-700 rounded mb-3 flex items-center justify-center relative">
              {/* Frame */}
              <svg viewBox="0 0 100 100" className="w-24 h-24">
                {/* NATO Frame */}
                <rect
                  x="5" y="20" width="90" height="60"
                  fill="none"
                  stroke={sideColors[selectedSide]}
                  strokeWidth="4"
                />
                {/* Main Icon */}
                <path
                  d={symbol.path}
                  stroke={selectedSide === 'enemy' ? '#F44336' : '#FFF'}
                  strokeWidth="6"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {/* Affiliation indicator */}
              <div
                className="absolute top-2 right-2 w-4 h-4 rounded-full border-2 border-white"
                style={{ backgroundColor: sideColors[selectedSide] }}
              />
            </div>

            {/* Symbol Info */}
            <div className="text-center">
              <div className="font-bold text-lg">{symbol.nameJa}</div>
              <div className="text-sm text-gray-400">{symbol.name}</div>
              <div className="text-xs text-gray-500 mt-1">{symbol.category}</div>
            </div>

            {/* Description */}
            <div className="mt-2 text-xs text-gray-500 text-center">
              {symbol.description}
            </div>
          </div>
        ))}
      </div>

      {/* Reference Table */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-blue-400 mb-4">Symbol Reference</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-4 py-2 text-left">ID</th>
                <th className="px-4 py-2 text-left">Japanese</th>
                <th className="px-4 py-2 text-left">English</th>
                <th className="px-4 py-2 text-left">Category</th>
                <th className="px-4 py-2 text-left">Description</th>
              </tr>
            </thead>
            <tbody className="bg-gray-900">
              {natoSymbols.map((symbol) => (
                <tr key={symbol.id} className="border-t border-gray-800">
                  <td className="px-4 py-2 font-mono text-blue-300">{symbol.id}</td>
                  <td className="px-4 py-2">{symbol.nameJa}</td>
                  <td className="px-4 py-2 text-gray-400">{symbol.name}</td>
                  <td className="px-4 py-2 text-gray-500">{symbol.category}</td>
                  <td className="px-4 py-2 text-gray-500">{symbol.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Back to Game */}
      <div className="mt-8">
        <a
          href="/game"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg"
        >
          ← ゲームに戻る
        </a>
      </div>
    </div>
  );
}
