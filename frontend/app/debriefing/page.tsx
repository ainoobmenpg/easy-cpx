'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import API from '../lib/api';

interface DebriefingData {
  game_id: number;
  game_name: string;
  scenario_id: string;
  total_turns: number;
  duration: {
    start_date: string;
    start_time: string;
    end_date: string;
    end_turn: number;
  };
  statistics: {
    player: {
      initial_count: number;
      destroyed: number;
      damaged: number;
      light_damage: number;
      intact: number;
      casualty_rate: number;
      average_strength: number;
    };
    enemy: {
      initial_count: number;
      destroyed: number;
      damaged: number;
      light_damage: number;
      destruction_rate: number;
    };
    resources: {
      ammo_depleted_units: number;
      ammo_low_units: number;
      fuel_depleted_units: number;
      fuel_low_units: number;
      readiness_degraded: number;
    };
    operations: {
      total_turns: number;
      total_orders: number;
    };
  };
  mission_result: {
    status: 'success' | 'partial' | 'failed';
    description: string;
    player_casualty_rate: number;
    enemy_destruction_rate: number;
  };
  grade: string;
  commentary: string;
  recommendations: string[];
}

function DebriefingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const gameId = searchParams.get('gameId');

  const [debriefing, setDebriefing] = useState<DebriefingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) {
      setError('Game ID not provided');
      setLoading(false);
      return;
    }

    fetch(API.gameDebriefing(gameId))
      .then(res => {
        if (!res.ok) {
          return res.text().then(text => {
            throw new Error(`HTTP ${res.status}: ${text}`);
          });
        }
        return res.json();
      })
      .then(data => {
        setDebriefing(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [gameId]);

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'S': return 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white';
      case 'A': return 'bg-green-500 text-white';
      case 'B': return 'bg-blue-500 text-white';
      case 'C': return 'bg-yellow-500 text-black';
      case 'D': return 'bg-red-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-400';
      case 'partial': return 'text-yellow-400';
      case 'failed': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-blue-400 text-xl">ミッション評価を読み込み中...</div>
      </div>
    );
  }

  if (error || !debriefing) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-red-900/50 border border-red-500 p-6 rounded-lg text-center">
          <p className="text-red-200 mb-4">{error || 'ミッション評価の読み込みに失敗しました'}</p>
          <button
            onClick={() => router.push('/scenarios')}
            className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded"
          >
            Back to Scenarios
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="bg-gray-800/90 border-b border-gray-700/50 px-6 py-4 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            Debriefing Report
          </h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Grade Section */}
        <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-blue-300">Mission Result</h2>
              <p className={`text-lg font-bold mt-1 ${getStatusColor(debriefing.mission_result.status)}`}>
                {debriefing.mission_result.status.toUpperCase()}
              </p>
            </div>
            <div className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold shadow-lg ${getGradeColor(debriefing.grade)}`}>
              {debriefing.grade}
            </div>
          </div>
          <p className="text-gray-400 mt-4">{debriefing.mission_result.description}</p>
        </div>

        {/* Statistics Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Player Losses */}
          <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-blue-300 mb-4">Player Forces</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Initial Units</span>
                <span className="font-bold">{debriefing.statistics.player.initial_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Destroyed</span>
                <span className="font-bold text-red-400">{debriefing.statistics.player.destroyed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Damaged</span>
                <span className="font-bold text-yellow-400">{debriefing.statistics.player.damaged}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Intact</span>
                <span className="font-bold text-green-400">{debriefing.statistics.player.intact}</span>
              </div>
              <div className="border-t border-gray-700 pt-3 mt-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Casualty Rate</span>
                  <span className="font-bold text-red-400">{debriefing.statistics.player.casualty_rate}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Enemy Losses */}
          <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-red-300 mb-4">Enemy Forces</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Initial Units</span>
                <span className="font-bold">{debriefing.statistics.enemy.initial_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Destroyed</span>
                <span className="font-bold text-green-400">{debriefing.statistics.enemy.destroyed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Damaged</span>
                <span className="font-bold text-yellow-400">{debriefing.statistics.enemy.damaged}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Light Damage</span>
                <span className="font-bold text-blue-400">{debriefing.statistics.enemy.light_damage}</span>
              </div>
              <div className="border-t border-gray-700 pt-3 mt-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Destruction Rate</span>
                  <span className="font-bold text-green-400">{debriefing.statistics.enemy.destruction_rate}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Operations Summary */}
        <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-bold text-gray-300 mb-4">Operations Summary</h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-400">{debriefing.total_turns}</div>
              <div className="text-sm text-gray-500">Total Turns</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-400">{debriefing.statistics.operations.total_orders}</div>
              <div className="text-sm text-gray-500">Orders Issued</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-400">{debriefing.statistics.player.average_strength}%</div>
              <div className="text-sm text-gray-500">Avg Strength</div>
            </div>
          </div>
        </div>

        {/* Resource Status */}
        <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-bold text-gray-300 mb-4">Resource Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-900/50 rounded-lg">
              <div className="text-xl font-bold text-red-400">{debriefing.statistics.resources.ammo_depleted_units}</div>
              <div className="text-xs text-gray-500">Ammo Depleted</div>
            </div>
            <div className="text-center p-3 bg-gray-900/50 rounded-lg">
              <div className="text-xl font-bold text-yellow-400">{debriefing.statistics.resources.ammo_low_units}</div>
              <div className="text-xs text-gray-500">Ammo Low</div>
            </div>
            <div className="text-center p-3 bg-gray-900/50 rounded-lg">
              <div className="text-xl font-bold text-red-400">{debriefing.statistics.resources.fuel_depleted_units}</div>
              <div className="text-xs text-gray-500">Fuel Depleted</div>
            </div>
            <div className="text-center p-3 bg-gray-900/50 rounded-lg">
              <div className="text-xl font-bold text-yellow-400">{debriefing.statistics.resources.fuel_low_units}</div>
              <div className="text-xs text-gray-500">Fuel Low</div>
            </div>
          </div>
        </div>

        {/* Commentary */}
        <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-bold text-gray-300 mb-4">Command Commentary</h3>
          <p className="text-gray-300 leading-relaxed">{debriefing.commentary}</p>
        </div>

        {/* Recommendations */}
        <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-bold text-gray-300 mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {debriefing.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-gray-300">
                <span className="text-blue-400 mt-1">&#9654;</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-4">
          <button
            onClick={() => router.push(`/game?gameId=${gameId}`)}
            className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg transition-colors"
          >
            ミッション再挑戦
          </button>
          <button
            onClick={() => router.push('/scenarios')}
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors"
          >
            シナリオ選択へ
          </button>
        </div>
      </main>
    </div>
  );
}

export default function DebriefingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-blue-400 text-xl">読み込み中...</div>
      </div>
    }>
      <DebriefingContent />
    </Suspense>
  );
}
