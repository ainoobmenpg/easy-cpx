'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'next-i18next';
import API from './api';

export type ConnectionStatus = 'healthy' | 'timeout' | 'mismatch' | 'unknown';

interface HealthResponse {
  status: string;
  version?: string;
  timestamp?: string;
}

export interface ConnectionState {
  status: ConnectionStatus;
  latency?: number;
  healthResponse?: HealthResponse;
  error?: string;
}

// Check if the API URL matches the recommended one
const getRecommendedUrl = (): string => {
  if (typeof window !== 'undefined') {
    // Default recommended URL for local development
    return 'http://localhost:8000';
  }
  return 'http://localhost:8000';
};

export const checkConnection = async (): Promise<ConnectionState> => {
  const startTime = Date.now();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API.baseUrl}/health`, {
      method: 'GET',
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json' }
    });

    clearTimeout(timeoutId);
    const latency = Date.now() - startTime;

    if (!response.ok) {
      return {
        status: 'mismatch',
        latency,
        error: `HTTP ${response.status}`
      };
    }

    const data = await response.json() as HealthResponse;

    return {
      status: 'healthy',
      latency,
      healthResponse: data
    };
  } catch (error) {
    const latency = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    if (error instanceof DOMException && error.name === 'AbortError') {
      return {
        status: 'timeout',
        latency,
        error: 'Request timed out'
      };
    }

    return {
      status: 'mismatch',
      latency,
      error: errorMessage
    };
  }
};

interface ConnectionBadgeProps {
  onClick?: () => void;
}

export function ConnectionBadge({ onClick }: ConnectionBadgeProps) {
  const { t } = useTranslation();
  const [connectionState, setConnectionState] = useState<ConnectionState>({ status: 'unknown' });
  const [isChecking, setIsChecking] = useState(false);

  const check = useCallback(async () => {
    setIsChecking(true);
    const result = await checkConnection();
    setConnectionState(result);
    setIsChecking(false);
  }, []);

  useEffect(() => {
    // Initial check using async IIFE
    (async () => {
      const result = await checkConnection();
      setConnectionState(result);
    })();

    // Check connection every 30 seconds
    const interval = setInterval(async () => {
      const result = await checkConnection();
      setConnectionState(result);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    healthy: { color: 'bg-green-500', text: t('connection.connected'), textColor: 'text-green-600' },
    timeout: { color: 'bg-yellow-500', text: t('connection.timeout'), textColor: 'text-yellow-600' },
    mismatch: { color: 'bg-red-500', text: t('connection.error'), textColor: 'text-red-600' },
    unknown: { color: 'bg-gray-400', text: t('connection.unknown'), textColor: 'text-gray-500' }
  };

  const config = statusConfig[connectionState.status];
  const latencyText = connectionState.latency ? `${connectionState.latency}ms` : '';

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all hover:scale-105 ${config.color} text-white shadow-md`}
      disabled={isChecking}
      title={connectionState.error || `Click to diagnostics (${latencyText || 'checking...'})`}
    >
      <span className={`w-2 h-2 rounded-full ${connectionState.status === 'healthy' ? 'bg-white' : 'bg-white/50'}`} />
      <span>{config.text}</span>
      {connectionState.latency && (
        <span className="text-xs opacity-75 ml-1">{connectionState.latency}ms</span>
      )}
      {isChecking && (
        <span className="text-xs">...</span>
      )}
    </button>
  );
}

interface DiagnosticModalProps {
  isOpen: boolean;
  onClose: () => void;
  connectionState: ConnectionState;
  onRetry: () => void;
}

export function DiagnosticModal({ isOpen, onClose, connectionState, onRetry }: DiagnosticModalProps) {
  const { t } = useTranslation();
  if (!isOpen) return null;

  const recommendedUrl = getRecommendedUrl();
  const currentUrl = API.baseUrl;
  const isUrlMatch = currentUrl === recommendedUrl;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">{t('connection.diagnostic')}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
          >
            &times;
          </button>
        </div>

        <div className="space-y-4">
          {/* Status */}
          <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">{t('connection.status')}</h3>
            <div className="flex items-center gap-2">
              <span className={`w-3 h-3 rounded-full ${
                connectionState.status === 'healthy' ? 'bg-green-500' :
                connectionState.status === 'timeout' ? 'bg-yellow-500' :
                'bg-red-500'
              }`} />
              <span className="text-gray-700 dark:text-gray-300">
                {connectionState.status === 'healthy' ? t('connection.healthy') :
                 connectionState.status === 'timeout' ? t('connection.timeout') : t('connection.error')}
              </span>
              {connectionState.latency && (
                <span className="text-sm text-gray-500 ml-2">({connectionState.latency}ms)</span>
              )}
            </div>
            {connectionState.error && (
              <p className="text-sm text-red-500 mt-1">{connectionState.error}</p>
            )}
          </div>

          {/* Current URL */}
          <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">{t('connection.currentUrl')}</h3>
            <code className="text-sm bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded break-all">
              {currentUrl}
            </code>
            {!isUrlMatch && (
              <p className="text-sm text-yellow-600 mt-2">
                {t('connection.differentFromRecommended')}
              </p>
            )}
          </div>

          {/* Recommended URL */}
          <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">{t('connection.recommendedUrl')}</h3>
            <code className="text-sm bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
              {recommendedUrl}
            </code>
          </div>

          {/* Health Response */}
          {connectionState.healthResponse && (
            <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">{t('connection.serverInfo')}</h3>
              <pre className="text-xs bg-gray-200 dark:bg-gray-600 p-2 rounded overflow-x-auto">
                {JSON.stringify(connectionState.healthResponse, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            {t('connection.retryTest')}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-800 dark:text-white rounded-lg transition-colors"
          >
            {t('connection.close')}
          </button>
        </div>
      </div>
    </div>
  );
}

// Hook for connection checking with games redirect
export function useConnectionCheck(router: ReturnType<typeof import('next/navigation').useRouter>) {
  const [connectionState, setConnectionState] = useState<ConnectionState>({ status: 'unknown' });
  const [gamesError, setGamesError] = useState<string | null>(null);

  const checkGamesConnection = useCallback(async () => {
    const result = await checkConnection();
    setConnectionState(result);

    // If connection is healthy, also check if games endpoint works
    if (result.status === 'healthy') {
      try {
        const response = await fetch(`${API.baseUrl}/api/games/`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
          setGamesError(`Games API error: ${response.status}`);
        } else {
          setGamesError(null);
        }
      } catch (error) {
        setGamesError(error instanceof Error ? error.message : 'Unknown error');
      }
    }

    return result;
  }, []);

  // Check if we should redirect to /games
  useEffect(() => {
    const check = async () => {
      const result = await checkGamesConnection();

      // If connection is not healthy, suggest /games
      if (result.status !== 'healthy') {
        // User can decide to navigate or stay
        console.warn('API connection issue detected:', result.error);
      }
    };

    check();
  }, [checkGamesConnection, router]);

  return { connectionState, gamesError, checkGamesConnection };
}
