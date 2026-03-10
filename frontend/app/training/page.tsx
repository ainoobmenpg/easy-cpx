"use client";

import { useState, useEffect } from "react";
import API from "../lib/api";
import { useI18n } from "../lib/i18n";
import LanguageSwitcher from "../lib/language-switcher";

interface TrainingMetrics {
  current_turn: number;
  ccir_achievement_rate: number;
  roe_compliance_rate: number;
  casualty_efficiency: number;
  time_performance: number;
  overall_score: number;
}

interface ScoreboardSummary {
  game_id: number;
  overall_score: number;
  grade: string;
  star_rating: number;
  ccir: {
    ccirs: Array<{
      id: string;
      description: string;
      priority: string;
      achieved: boolean;
      current_value: number;
      target_value: number;
    }>;
    achievement_rate: number;
    total: number;
    achieved: number;
  };
  roe: {
    compliance_rate: number;
    total_violations: number;
    total_warnings: number;
  };
  casualty_efficiency: {
    efficiency_ratio: number;
    player_preservation: number;
    enemy_destruction: number;
    player_losses: { destroyed: number; damaged: number; total: number };
    enemy_losses: { destroyed: number; damaged: number; total: number };
  };
  time_performance: {
    target_turns: number;
    current_turn: number;
    achievement_rate: number;
    within_target: boolean;
  };
  turn_history: Array<{
    turn: number;
    ccir_rate: number;
    roe_rate: number;
    efficiency: number;
    time_rate: number;
  }>;
}

export default function TrainingDashboard() {
  const { t } = useI18n();
  const [gameId, setGameId] = useState<number>(1);
  const [metrics, setMetrics] = useState<TrainingMetrics | null>(null);
  const [summary, setSummary] = useState<ScoreboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  const fetchMetrics = async () => {
    try {
      const res = await fetch(API.trainingMetrics(gameId));
      const data = await res.json();
      if (!data.error) {
        setMetrics(data);
      }
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(API.trainingSummary(gameId));
      const data = await res.json();
      if (!data.error) {
        setSummary(data);
      }
    } catch (err) {
      console.error("Failed to fetch summary:", err);
    }
  };

  const initializeScoreboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(API.trainingInitialize, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_id: gameId,
          player_units: 10,
          enemy_units: 12,
          target_turns: 10,
        }),
      });
      const data = await res.json();
      if (data.status === "initialized") {
        setInitialized(true);
        await fetchMetrics();
        await fetchSummary();
      } else {
        setError(data.error || t('training.error.initFailed'));
      }
    } catch (err) {
      setError(t('training.error.initFailed'));
    } finally {
      setLoading(false);
    }
  };

  const finalizeScoreboard = async () => {
    setLoading(true);
    try {
      const res = await fetch(API.trainingFinalize, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id: gameId }),
      });
      const data = await res.json();
      if (data.status === "finalized") {
        await fetchSummary();
      }
    } catch (err) {
      setError(t('training.error.finalizeFailed'));
    } finally {
      setLoading(false);
    }
  };

  const simulateTurn = async () => {
    setLoading(true);
    try {
      const res = await fetch(API.trainingUpdate, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_id: gameId,
          turn_number: (metrics?.current_turn || 0) + 1,
          player_destroyed: Math.floor(Math.random() * 2),
          enemy_destroyed: Math.floor(Math.random() * 3) + 1,
          player_damaged: Math.floor(Math.random() * 2),
          enemy_damaged: Math.floor(Math.random() * 2),
        }),
      });
      const data = await res.json();
      if (data.status === "updated") {
        await fetchMetrics();
        await fetchSummary();
      }
    } catch (err) {
      setError(t('training.error.updateFailed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialized) {
      fetchMetrics();
      const interval = setInterval(fetchMetrics, 5000);
      return () => clearInterval(interval);
    }
  }, [initialized]);

  const getGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      S: "text-yellow-400",
      A: "text-green-400",
      B: "text-blue-400",
      C: "text-orange-400",
      D: "text-red-400",
      F: "text-red-600",
    };
    return colors[grade] || "text-gray-400";
  };

  const getGradeBg = (grade: string) => {
    const colors: Record<string, string> = {
      S: "bg-yellow-900",
      A: "bg-green-900",
      B: "bg-blue-900",
      C: "bg-orange-900",
      D: "bg-red-900",
      F: "bg-red-950",
    };
    return colors[grade] || "bg-gray-900";
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      critical: "bg-red-600",
      high: "bg-orange-500",
      medium: "bg-yellow-500",
      low: "bg-blue-500",
    };
    return colors[priority] || "bg-gray-500";
  };

  const getProgressBarColor = (rate: number) => {
    if (rate >= 80) return "bg-green-500";
    if (rate >= 60) return "bg-yellow-500";
    if (rate >= 40) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">
              {t('training.title')}
            </h1>
            <p className="text-gray-400 mt-2">
              {t('training.ccirAchievement')} / {t('training.roeCompliance')} / {t('training.casualtyEfficiency')} / {t('training.timePerformance')}
            </p>
          </div>
          <LanguageSwitcher />
        </header>

        {!initialized && (
          <div className="bg-gray-900 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">{t('training.initializeSession')}</h2>
            <div className="flex gap-4 items-center">
              <div>
                <label className="block text-sm text-gray-400 mb-1">{t('training.gameId')}</label>
                <input
                  type="number"
                  value={gameId}
                  onChange={(e) => setGameId(Number(e.target.value))}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 w-32"
                />
              </div>
              <button
                onClick={initializeScoreboard}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-medium mt-5 disabled:opacity-50"
              >
                {loading ? t('training.processing') : t('training.startTraining')}
              </button>
            </div>
            {error && <p className="text-red-400 mt-3">{error}</p>}
          </div>
        )}

        {initialized && metrics && (
          <>
            {/* Main Score Display */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              {/* Overall Score */}
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-sm text-gray-400 uppercase mb-2">{t('training.overallScore')}</h3>
                <div className="text-4xl font-bold text-white">
                  {metrics.overall_score}
                  <span className="text-lg text-gray-500">/100</span>
                </div>
                <div className="mt-2 text-sm text-gray-400">{t('training.turn')} {metrics.current_turn}</div>
              </div>

              {/* CCIR Achievement */}
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-sm text-gray-400 uppercase mb-2">{t('training.ccirAchievement')}</h3>
                <div className="text-4xl font-bold">
                  <span className={getProgressBarColor(metrics.ccir_achievement_rate).replace("bg-", "text-")}>
                    {metrics.ccir_achievement_rate}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-gray-800 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getProgressBarColor(metrics.ccir_achievement_rate)}`}
                    style={{ width: `${metrics.ccir_achievement_rate}%` }}
                  />
                </div>
              </div>

              {/* ROE Compliance */}
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-sm text-gray-400 uppercase mb-2">{t('training.roeCompliance')}</h3>
                <div className="text-4xl font-bold">
                  <span className={getProgressBarColor(metrics.roe_compliance_rate).replace("bg-", "text-")}>
                    {metrics.roe_compliance_rate}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-gray-800 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getProgressBarColor(metrics.roe_compliance_rate)}`}
                    style={{ width: `${metrics.roe_compliance_rate}%` }}
                  />
                </div>
              </div>

              {/* Time Performance */}
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-sm text-gray-400 uppercase mb-2">{t('training.timePerformance')}</h3>
                <div className="text-4xl font-bold">
                  <span className={getProgressBarColor(metrics.time_performance).replace("bg-", "text-")}>
                    {metrics.time_performance}%
                  </span>
                </div>
                <div className="mt-2 text-sm text-gray-400">
                  {t('training.efficiency')}: {metrics.casualty_efficiency}x
                </div>
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex gap-4 mb-6">
              <button
                onClick={simulateTurn}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded font-medium disabled:opacity-50"
              >
                {loading ? t('training.processing') : t('training.simulateTurn')}
              </button>
              <button
                onClick={finalizeScoreboard}
                disabled={loading}
                className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded font-medium disabled:opacity-50"
              >
                {t('training.finalizeGrade')}
              </button>
            </div>
          </>
        )}

        {/* Final Grade Display */}
        {summary && summary.grade && (
          <div className={`${getGradeBg(summary.grade)} rounded-lg p-8 mb-6 text-center`}>
            <h2 className="text-2xl font-bold mb-4">{t('training.finalAssessment')}</h2>
            <div className="flex items-center justify-center gap-8">
              {/* Star Rating */}
              <div className="text-6xl">
                {[1, 2, 3, 4, 5].map((star) => (
                  <span
                    key={star}
                    className={star <= summary.star_rating ? "text-yellow-400" : "text-gray-600"}
                  >
                    ★
                  </span>
                ))}
              </div>
              {/* Grade */}
              <div className={`text-8xl font-bold ${getGradeColor(summary.grade)}`}>
                {summary.grade}
              </div>
              {/* Score */}
              <div className="text-2xl">
                <div className="text-gray-400">{t('training.overallScore')}</div>
                <div className="font-bold text-white">{summary.overall_score}</div>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Metrics */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CCIR Details */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">{t('training.ccirStatus')}</h3>
              <div className="space-y-3">
                {summary.ccir.ccirs.map((ccir) => (
                  <div key={ccir.id} className="flex items-center gap-3">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        ccir.achieved ? "bg-green-500" : "bg-gray-500"
                      }`}
                    />
                    <span className="flex-1">{ccir.description}</span>
                    <span
                      className={`px-2 py-1 rounded text-xs ${getPriorityColor(
                        ccir.priority
                      )}`}
                    >
                      {ccir.priority}
                    </span>
                    <span className="text-sm text-gray-400">
                      {ccir.current_value}/{ccir.target_value}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-800">
                <div className="text-sm text-gray-400">
                  {t('training.achievement')}: {summary.ccir.achieved}/{summary.ccir.total} (
                  {summary.ccir.achievement_rate}%)
                </div>
              </div>
            </div>

            {/* ROE Details */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">{t('training.roeCompliance')}</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">{t('training.achievementRate')}</span>
                    <span>{summary.roe.compliance_rate}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getProgressBarColor(
                        summary.roe.compliance_rate
                      )}`}
                      style={{ width: `${summary.roe.compliance_rate}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-gray-800 rounded p-3">
                    <div className="text-2xl font-bold text-red-400">
                      {summary.roe.total_violations}
                    </div>
                    <div className="text-sm text-gray-400">{t('training.violations')}</div>
                  </div>
                  <div className="bg-gray-800 rounded p-3">
                    <div className="text-2xl font-bold text-yellow-400">
                      {summary.roe.total_warnings}
                    </div>
                    <div className="text-sm text-gray-400">{t('training.warnings')}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Casualty Efficiency */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">{t('training.casualtyEfficiency')}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 rounded p-4">
                  <div className="text-sm text-gray-400 mb-1">{t('training.efficiencyRatio')}</div>
                  <div className="text-2xl font-bold text-white">
                    {summary.casualty_efficiency.efficiency_ratio === Infinity
                      ? "∞"
                      : `${summary.casualty_efficiency.efficiency_ratio}x`}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-4">
                  <div className="text-sm text-gray-400 mb-1">{t('training.preservation')}</div>
                  <div className="text-2xl font-bold text-green-400">
                    {summary.casualty_efficiency.player_preservation}%
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-4">
                  <div className="text-sm text-gray-400 mb-1">{t('training.playerLosses')}</div>
                  <div className="text-xl font-bold text-red-400">
                    {summary.casualty_efficiency.player_losses.destroyed} {t('training.destroyed')},{" "}
                    {summary.casualty_efficiency.player_losses.damaged} {t('training.damaged')}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-4">
                  <div className="text-sm text-gray-400 mb-1">{t('training.enemyLosses')}</div>
                  <div className="text-xl font-bold text-green-400">
                    {summary.casualty_efficiency.enemy_losses.destroyed} {t('training.destroyed')},{" "}
                    {summary.casualty_efficiency.enemy_losses.damaged} {t('training.damaged')}
                  </div>
                </div>
              </div>
            </div>

            {/* Time Performance */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">{t('training.timePerformance')}</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">{t('training.targetTurns')}</span>
                  <span className="font-bold">{summary.time_performance.target_turns}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">{t('training.currentTurn')}</span>
                  <span className="font-bold">{summary.time_performance.current_turn}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">{t('training.withinTarget')}</span>
                  <span
                    className={`font-bold ${
                      summary.time_performance.within_target
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    {summary.time_performance.within_target ? t('training.yes') : t('training.no')}
                  </span>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">{t('training.achievementRate')}</span>
                    <span>{summary.time_performance.achievement_rate}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getProgressBarColor(
                        summary.time_performance.achievement_rate
                      )}`}
                      style={{ width: `${summary.time_performance.achievement_rate}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Turn History Chart */}
        {summary && summary.turn_history.length > 0 && (
          <div className="bg-gray-900 rounded-lg p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">{t('training.turnHistory')}</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left py-2 px-3 text-gray-400">{t('training.turn')}</th>
                    <th className="text-left py-2 px-3 text-gray-400">{t('training.ccirRate')}</th>
                    <th className="text-left py-2 px-3 text-gray-400">{t('training.roeRate')}</th>
                    <th className="text-left py-2 px-3 text-gray-400">{t('training.efficiency')}</th>
                    <th className="text-left py-2 px-3 text-gray-400">{t('training.timeRate')}</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.turn_history.map((turn) => (
                    <tr key={turn.turn} className="border-b border-gray-800">
                      <td className="py-2 px-3 font-medium">{turn.turn}</td>
                      <td className="py-2 px-3">{turn.ccir_rate}%</td>
                      <td className="py-2 px-3">{turn.roe_rate}%</td>
                      <td className="py-2 px-3">{turn.efficiency}x</td>
                      <td className="py-2 px-3">{turn.time_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
