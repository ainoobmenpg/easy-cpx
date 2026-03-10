'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import API from '../lib/api';
import { useI18n } from '../lib/i18n';
import LanguageSwitcher from '../lib/language-switcher';
import { ConnectionBadge, DiagnosticModal, checkConnection, ConnectionState } from '../lib/connection-indicator';
import { GameCardSkeleton } from '../components/Skeleton';
import ErrorDisplay from '../components/ErrorDisplay';

interface GameSummary {
  id: number;
  name: string;
  current_turn: number;
  current_date: string;
  current_time: string;
  weather: string;
  phase: string;
  is_active: boolean;
}

export default function GamesPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [diagnosticOpen, setDiagnosticOpen] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>({ status: 'unknown' });

  useEffect(() => {
    fetch(API.games)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Games loaded:', data);
        setGames(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load games:', err);
        setError(t('games.error'));
        setLoading(false);
      });
  }, []);

  // Check connection status on mount
  useEffect(() => {
    (async () => {
      const result = await checkConnection();
      setConnectionState(result);
    })();
  }, []);

  const handleRetry = async () => {
    const result = await checkConnection();
    setConnectionState(result);
  };

  const getPhaseLabel = (phase: string) => {
    const key = `phase.${phase}` as const;
    return t(key) || phase;
  };

  const getWeatherLabel = (weather: string) => {
    const key = `weather.${weather}` as const;
    return t(key) || weather;
  };

  const getStatusBadge = (game: GameSummary) => {
    if (!game.is_active) {
      return <span className="text-xs px-2 py-1 rounded bg-gray-600 text-gray-300">{t('games.status.ended')}</span>;
    }
    switch (game.phase) {
      case 'orders':
        return <span className="text-xs px-2 py-1 rounded bg-blue-600 text-white">{t('games.status.active')}</span>;
      case 'adjudication':
        return <span className="text-xs px-2 py-1 rounded bg-yellow-600 text-white">{t('games.status.adjudicating')}</span>;
      case 'sitrep':
        return <span className="text-xs px-2 py-1 rounded bg-green-600 text-white">{t('phase.sitrep')}</span>;
      default:
        return <span className="text-xs px-2 py-1 rounded bg-gray-600 text-gray-300">{game.phase}</span>;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <header className="bg-gray-800/90 border-b border-gray-700/50 px-6 py-4 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              {t('common.gameTitle')} - {t('games.title')}
            </h1>
            <div className="flex gap-3 items-center">
              <ConnectionBadge onClick={() => setDiagnosticOpen(true)} />
              <LanguageSwitcher />
              <button
                onClick={() => router.push('/scenarios')}
                aria-label={t('common.newGame')}
                className="text-sm bg-green-600 hover:bg-green-500 px-4 py-2 rounded transition-colors"
              >
                {t('common.newGame')}
              </button>
              <button
                onClick={() => router.push('/')}
                aria-label={t('common.back')}
                className="text-sm bg-gray-700/50 hover:bg-gray-600/50 px-4 py-2 rounded transition-colors"
              >
                {t('common.back')}
              </button>
            </div>
          </div>
        </header>
        <main className="max-w-6xl mx-auto p-6 space-y-4">
          {[1, 2, 3].map(i => <GameCardSkeleton key={i} />)}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="bg-gray-800/90 border-b border-gray-700/50 px-6 py-4 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            {t('common.gameTitle')} - {t('games.title')}
          </h1>
          <div className="flex gap-3 items-center">
            <LanguageSwitcher />
            <button
              onClick={() => router.push('/scenarios')}
              className="text-sm bg-green-600 hover:bg-green-500 px-4 py-2 rounded transition-colors"
            >
              {t('common.newGame')}
            </button>
            <button
              onClick={() => router.push('/')}
              className="text-sm bg-gray-700/50 hover:bg-gray-600/50 px-4 py-2 rounded transition-colors"
            >
              {t('common.back')}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        {error && (
          <ErrorDisplay
            message={error}
            title={t('games.errorTitle')}
            onRetry={() => {
              setError(null);
              setLoading(true);
              fetch(API.games)
                .then(res => {
                  if (!res.ok) throw new Error(`HTTP ${res.status}`);
                  return res.json();
                })
                .then(data => {
                  setGames(Array.isArray(data) ? data : []);
                  setLoading(false);
                })
                .catch(err => {
                  setError(t('games.error'));
                  setLoading(false);
                });
            }}
            className="mb-6"
          />
        )}

        {games.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg mb-6">{t('games.noGames')}</p>
            <button
              onClick={() => router.push('/scenarios')}
              className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              {t('games.newGame')}
            </button>
          </div>
        ) : (
          <>
            <p className="text-gray-400 mb-6 text-center">
              {t('games.selectOrCreate')}
            </p>

            <div className="space-y-4">
              {games.map((game) => (
                <div
                  key={game.id}
                  className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-5 hover:border-gray-600/50 transition-all cursor-pointer hover:shadow-lg hover:shadow-gray-900/20"
                  onClick={() => router.push(`/game?gameId=${game.id}`)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-xl font-bold text-blue-300">{game.name}</h2>
                        {getStatusBadge(game)}
                      </div>
                      <div className="flex items-center gap-6 text-sm text-gray-400">
                        <span>{t('games.turn')}: {game.current_turn}</span>
                        <span>{t('games.date')}: {game.current_date}</span>
                        <span>{t('games.time')}: {game.current_time}</span>
                        <span>{t('games.weather')}: {getWeatherLabel(game.weather)}</span>
                        <span>{t('games.phase')}: {getPhaseLabel(game.phase)}</span>
                      </div>
                    </div>
                    <div className="text-gray-500">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
      <DiagnosticModal
        isOpen={diagnosticOpen}
        onClose={() => setDiagnosticOpen(false)}
        connectionState={connectionState}
        onRetry={handleRetry}
      />
    </div>
  );
}
