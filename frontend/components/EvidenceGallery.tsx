'use client';

import React from 'react';
import { useFilterStore } from '../store/useFilterStore';
import { useTranslations } from 'next-intl';
import { Image as ImageIcon, ExternalLink } from 'lucide-react';
import { ViolationOverlay } from './VideoPlayerWithOverlay';

interface EvidenceGalleryProps {
  violations: ViolationOverlay[];
  onSelectCrop: (timestamp: number) => void;
}

export default function EvidenceGallery({
  violations,
  onSelectCrop,
}: EvidenceGalleryProps) {
  const t = useTranslations('results');
  const confidenceThreshold = useFilterStore((state) => state.confidenceThreshold);

  const evidenceViolations = violations.filter(
    (v) => v.label === 'non-helmet' && v.confidence >= confidenceThreshold
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
      <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-800">
        <ImageIcon className="w-5 h-5 text-sky-400" />
        {t('gallery')}
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-y-auto max-h-[350px] pr-1">
        {evidenceViolations.length > 0 ? (
          evidenceViolations.map((v) => {
            const cropUrl = v.image_url || v.imageUrl;

            return (
              <div
                key={v.id}
                onClick={() => onSelectCrop(v.timestamp)}
                className="group relative bg-slate-950 border border-slate-800/80 rounded-lg overflow-hidden cursor-pointer hover:border-sky-500 transition aspect-square"
              >
                <div className="w-full h-full bg-slate-900 flex flex-col items-center justify-center text-slate-600 group-hover:text-sky-400 transition relative">
                  {cropUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={cropUrl}
                      alt="Violation Crop"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <ImageIcon className="w-8 h-8" />
                  )}
                  <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                    <ExternalLink className="w-6 h-6 text-white" />
                  </div>
                  <span className="absolute bottom-2 left-2 bg-rose-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                    {Math.round(v.confidence * 100)}%
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-full text-center py-8 text-slate-500 text-sm">
            {t('noViolations')}
          </div>
        )}
      </div>
    </div>
  );
}