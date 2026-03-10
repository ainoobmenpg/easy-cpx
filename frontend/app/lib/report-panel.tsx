'use client';

import { useState, useEffect } from 'react';
import API from './api';
import { useI18n } from './i18n';
import type { UnifiedReport } from '@shared/types';

interface ReportPanelProps {
  gameId: number;
  turn: number;
}

type ReportTab = 'plan' | 'sync' | 'situation' | 'sustain';

export default function ReportPanel({ gameId, turn }: ReportPanelProps) {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<ReportTab>('situation');
  const [report, setReport] = useState<UnifiedReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReport(activeTab);
  }, [gameId, turn, activeTab]);

  const fetchReport = async (format: ReportTab) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API.baseUrl}/api/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId,
          format: format,
          turn: turn
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setReport(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: ReportTab; label: string; desc: string }[] = [
    { id: 'plan', label: 'PLAN', desc: 'OPORD' },
    { id: 'sync', label: 'SYNC', desc: 'OPSUM' },
    { id: 'situation', label: 'SITUATION', desc: 'SITREP/INTSUM' },
    { id: 'sustain', label: 'SUSTAIN', desc: 'LOGSITREP' }
  ];

  const renderContent = () => {
    if (loading) {
      return <div className="p-4 text-gray-400">Loading report...</div>;
    }
    if (error) {
      return <div className="p-4 text-red-400">Error: {error}</div>;
    }
    if (!report) {
      return <div className="p-4 text-gray-400">No report data</div>;
    }

    const content = report.content as any;

    switch (activeTab) {
      case 'plan':
        return (
          <div className="p-4 text-sm">
            <h3 className="font-bold text-yellow-400 mb-2">OPORD - Commander's Plan</h3>
            <pre className="whitespace-pre-wrap text-gray-300">
              {JSON.stringify(content, null, 2)}
            </pre>
          </div>
        );
      case 'sync':
        return (
          <div className="p-4 text-sm">
            <h3 className="font-bold text-blue-400 mb-2">OPSUM - Operations Summary</h3>
            <div className="space-y-2">
              <div>
                <span className="text-gray-400">Period: </span>
                <span>{content.period}</span>
              </div>
              <div>
                <span className="text-gray-400">Assessment: </span>
                <span className="text-green-400">{content.commander_assessment}</span>
              </div>
              {content.operations_conducted?.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-400 mb-1">Operations Conducted:</div>
                  {content.operations_conducted.map((op: any, i: number) => (
                    <div key={i} className="ml-2 text-gray-300">
                      {op.operation_name}: {op.results} ({op.outcome})
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      case 'situation':
        return (
          <div className="p-4 text-sm">
            <h3 className="font-bold text-green-400 mb-2">INTSUM - Intelligence Summary</h3>
            <div className="space-y-2">
              <div>
                <span className="text-gray-400">Period: </span>
                <span>{content.period}</span>
              </div>
              <div>
                <span className="text-gray-400">Summary: </span>
                <span className="text-gray-300">{content.summary}</span>
              </div>
              {content.enemy_dispositions?.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-400 mb-1">Enemy Dispositions:</div>
                  {content.enemy_dispositions.map((e: any, i: number) => (
                    <div key={i} className="ml-2 text-gray-300">
                      {e.unit_name} @ {e.position} [{e.assessment}] - {e.strength}
                    </div>
                  ))}
                </div>
              )}
              {content.intelligence_gaps?.length > 0 && (
                <div className="mt-2 text-yellow-400">
                  Intelligence Gaps: {content.intelligence_gaps.join(', ')}
                </div>
              )}
              {content.recommendations?.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-400 mb-1">Recommendations:</div>
                  {content.recommendations.map((r: string, i: number) => (
                    <div key={i} className="ml-2 text-blue-300">- {r}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      case 'sustain':
        return (
          <div className="p-4 text-sm">
            <h3 className="font-bold text-orange-400 mb-2">LOGSITREP - Logistics Status</h3>
            <div className="space-y-2">
              <div>
                <span className="text-gray-400">Period: </span>
                <span>{content.period}</span>
              </div>
              {content.supply_status && (
                <div className="mt-2">
                  <div className="text-gray-400 mb-1">Supply Status:</div>
                  <div className="ml-2 space-y-1">
                    <div>
                      <span className="text-gray-400">Ammo: </span>
                      <span className="text-green-400">Full: {content.supply_status.ammo.full}</span>
                      <span className="text-yellow-400"> / Depleted: {content.supply_status.ammo.depleted}</span>
                      <span className="text-red-400"> / Exhausted: {content.supply_status.ammo.exhausted}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Fuel: </span>
                      <span className="text-green-400">Full: {content.supply_status.fuel.full}</span>
                      <span className="text-yellow-400"> / Depleted: {content.supply_status.fuel.depleted}</span>
                      <span className="text-red-400"> / Exhausted: {content.supply_status.fuel.exhausted}</span>
                    </div>
                  </div>
                </div>
              )}
              {content.supply_lines?.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-400 mb-1">Supply Lines:</div>
                  {content.supply_lines.map((line: any, i: number) => (
                    <div key={i} className="ml-2">
                      <span className={line.status === 'open' ? 'text-green-400' : 'text-red-400'}>
                        {line.status.toUpperCase()}
                      </span>
                      <span className="text-gray-400"> - {line.line_id}</span>
                    </div>
                  ))}
                </div>
              )}
              {content.resupply_requests?.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-400 mb-1">Resupply Requests:</div>
                  {content.resupply_requests.map((req: any, i: number) => (
                    <div key={i} className="ml-2 text-yellow-300">
                      {req.unit}: {req.type} ({req.priority}) - {req.status}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
      {/* Tab Bar */}
      <div className="flex border-b border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-3 py-2 text-xs font-mono transition-colors ${
              activeTab === tab.id
                ? 'bg-gray-800 text-white border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <div className="font-bold">{tab.label}</div>
            <div className="text-xs opacity-70">{tab.desc}</div>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="min-h-[200px] max-h-[400px] overflow-y-auto">
        {renderContent()}
      </div>
    </div>
  );
}
