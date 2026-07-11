'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Clock, ShieldAlert, ShieldCheck, FileText } from 'lucide-react';
import { ViolationOverlay } from './VideoPlayerWithOverlay';

interface ViolationTimelineProps {
  violations: ViolationOverlay[];
  currentTime: number;
  selectedId: string | null;
  onSelect: (violation: ViolationOverlay) => void;
}

export default function ViolationTimeline({
  violations,
  currentTime,
  selectedId,
  onSelect,
}: ViolationTimelineProps) {
  const t = useTranslations('results');

  // The parent already limits this to the pending, confidence-agnostic queue.
  const filteredViolations = violations;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col space-y-4 h-full">
      <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-800">
        <Clock className="w-5 h-5 text-sky-400" />
        {t('timeline')}
      </h3>

      <div className="space-y-2 overflow-y-auto max-h-[400px] flex-1 pr-1">
        {filteredViolations.length > 0 ? (
          filteredViolations.map((v) => {
            const isActive = v.id === selectedId;
            return (
              <button
                key={v.id}
                onClick={() => onSelect(v)}
                className={`w-full flex items-center justify-between p-3 rounded-lg border text-left transition cursor-pointer ${
                  isActive
                    ? 'bg-sky-950/40 border-sky-500 text-sky-300'
                    : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  {v.label === 'non-helmet' ? (
                    <ShieldAlert className="w-5 h-5 text-rose-500 flex-shrink-0" />
                  ) : v.label === 'helmet' ? (
                    <ShieldCheck className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  ) : (
                    <FileText className="w-5 h-5 text-sky-500 flex-shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-semibold capitalize">
                      {v.label === 'non-helmet' ? 'NO HELMET' : v.label}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Confidence: {Math.round(v.confidence * 100)}%
                    </p>
                  </div>
                </div>

                <span className="text-xs font-mono font-bold bg-slate-800 text-slate-300 px-2 py-1 rounded">
                  {formatTime(v.timestamp)}
                </span>
              </button>
            );
          })
        ) : (
          <div className="text-center py-10 text-slate-500 text-sm">
            {t('noViolations')}
          </div>
        )}
      </div>
    </div>
  );
}
