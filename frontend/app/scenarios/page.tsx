'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import API from '../lib/api';

interface Scenario {
  id: string;
  name: string;
  description: string;
  difficulty: 'easy' | 'normal' | 'hard';
  map_size: {
    width: number;
    height: number;
  };
}

// Fallback scenarios in case API fails
const FALLBACK_SCENARIOS: Scenario[] = [
  { id: 'defend-the-bridge', name: '橋の防衛', description: '敵の進撃を阻止し、橋を維持せよ', difficulty: 'normal', map_size: { width: 50, height: 50 } },
  { id: 'breakthrough', name: '突破口', description: '敵戦線を突破し、後方拠点占领せよ', difficulty: 'hard', map_size: { width: 60, height: 40 } },
  { id: 'counter-attack', name: '反撃', description: '敵の攻撃を撃退し、奪われた地域を奪還せよ', difficulty: 'easy', map_size: { width: 40, height: 40 } },
  { id: 'urban-assault', name: '都市攻略', description: '敵が占領した都市を奪還せよ', difficulty: 'hard', map_size: { width: 50, height: 40 } },
  { id: 'escort-mission', name: '護衛任務', description: '輸送補給部隊を護衛せよ', difficulty: 'normal', map_size: { width: 60, height: 50 } },
  { id: 'night-recon', name: '夜間偵察', description: '敵陣地の偵察任務', difficulty: 'easy', map_size: { width: 40, height: 40 } },
  { id: 'mountain-defense', name: '山岳防衛', description: '山岳地帯の要衝を防衛せよ', difficulty: 'normal', map_size: { width: 45, height: 45 } },
  { id: 'blitzkrieg', name: '電撃作戦', description: '快速装甲部隊で敵後方を奇襲せよ', difficulty: 'hard', map_size: { width: 70, height: 50 } },
];

export default function ScenariosPage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [startingGame, setStartingGame] = useState(false);

  useEffect(() => {
    fetch(API.scenarios)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Scenarios loaded:', data);
        setScenarios(Array.isArray(data) ? data : FALLBACK_SCENARIOS);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load scenarios:', err);
        // Use fallback scenarios
        setScenarios(FALLBACK_SCENARIOS);
        setLoading(false);
      });
  }, []);

  const handleStartGame = async (scenarioId: string) => {
    setStartingGame(true);
    try {
      const res = await fetch(API.gameStart, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: scenarioId,
          game_name: `Game-${Date.now()}`
        })
      });
      console.log('Start game response:', res.status);
      if (!res.ok) {
        const errText = await res.text();
        console.error('Start game error:', errText);
        setStartingGame(false);
        return;
      }
      const data = await res.json();
      console.log('Game started:', data);
      if (data.game_id) {
        router.push(`/game?gameId=${data.game_id}`);
      } else {
        console.error('No game_id in response:', data);
        setStartingGame(false);
      }
    } catch (err) {
      console.error('Failed to start game:', err);
      setStartingGame(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-600';
      case 'normal': return 'bg-yellow-600';
      case 'hard': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '簡単';
      case 'normal': return '普通';
      case 'hard': return '難しい';
      default: return difficulty;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-blue-400 text-xl">Loading scenarios...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="bg-gray-800/90 border-b border-gray-700/50 px-6 py-4 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            作戦級CPX - シナリオ選択
          </h1>
          <button
            onClick={() => router.push('/')}
            className="text-sm bg-gray-700/50 hover:bg-gray-600/50 px-4 py-2 rounded transition-colors"
          >
            Back
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <p className="text-gray-400 mb-8 text-center">
          シナリオを選択してください。各シナリオには異なる任務目標と難易度があります。
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              className={`bg-gray-800/80 border rounded-xl p-6 cursor-pointer transition-all hover:scale-[1.02] backdrop-blur-sm ${
                selectedScenario?.id === scenario.id
                  ? 'border-blue-500 shadow-lg shadow-blue-900/30'
                  : 'border-gray-700/50 hover:border-gray-600/50 hover:shadow-lg hover:shadow-gray-900/20'
              }`}
              onClick={() => setSelectedScenario(scenario)}
            >
              <div className="flex justify-between items-start mb-3">
                <h2 className="text-xl font-bold text-blue-300">{scenario.name}</h2>
                <span className={`text-xs px-2 py-1 rounded font-medium ${getDifficultyColor(scenario.difficulty)} text-white`}>
                  {getDifficultyLabel(scenario.difficulty)}
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-4 line-clamp-3">
                {scenario.description}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Map: {scenario.map_size.width}x{scenario.map_size.height}</span>
              </div>
            </div>
          ))}
        </div>

        {selectedScenario && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 max-w-lg w-full shadow-2xl">
              <h2 className="text-2xl font-bold text-blue-300 mb-3">{selectedScenario.name}</h2>
              <div className="mb-4">
                <span className={`text-xs px-2 py-1 rounded font-medium ${getDifficultyColor(selectedScenario.difficulty)} text-white`}>
                  {getDifficultyLabel(selectedScenario.difficulty)}
                </span>
              </div>
              <p className="text-gray-300 mb-6">{selectedScenario.description}</p>

              <div className="bg-gray-900/50 rounded-lg p-4 mb-6">
                <h3 className="text-sm font-bold text-gray-400 mb-2">マップ情報</h3>
                <div className="flex gap-6 text-sm">
                  <div>
                    <span className="text-gray-500">サイズ:</span>
                    <span className="text-gray-300 ml-2">{selectedScenario.map_size.width} x {selectedScenario.map_size.height}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => handleStartGame(selectedScenario.id)}
                  disabled={startingGame}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                >
                  {startingGame ? 'Starting...' : 'Start Mission'}
                </button>
                <button
                  onClick={() => setSelectedScenario(null)}
                  className="px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
