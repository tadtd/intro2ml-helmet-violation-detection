'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Image as ImageIcon } from 'lucide-react';
import { ViolationOverlay } from './VideoPlayerWithOverlay';

interface EvidenceGalleryProps {
  violations: ViolationOverlay[];
  selectedId: string | null;
  onSelect: (violation: ViolationOverlay) => void;
}

export default function EvidenceGallery({
  violations,
  selectedId,
  onSelect,
}: EvidenceGalleryProps) {
  const t = useTranslations('results');

  // Every non-helmet detection is shown regardless of confidence; the list is
  // the pending review queue, so reviewed items are already filtered out upstream.
  const evidenceViolations = violations;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
      <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-800">
        <ImageIcon className="w-5 h-5 text-sky-400" />
        {t('gallery')}
        <span className="text-xs font-normal text-slate-500">
          — bấm một ảnh để chọn, rồi phê duyệt ở khung bên phải
        </span>
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-y-auto max-h-[350px] pr-1">
        {evidenceViolations.length > 0 ? (
          evidenceViolations.map((v) => {
            const cropUrl = v.image_url || v.imageUrl;
            const isSelected = v.id === selectedId;

            return (
              <button
                key={v.id}
                onClick={() => onSelect(v)}
                className={`group relative bg-slate-950 rounded-lg overflow-hidden cursor-pointer transition aspect-square border-2 ${
                  isSelected ? 'border-sky-500 ring-2 ring-sky-500/40' : 'border-slate-800/80 hover:border-slate-600'
                }`}
              >
                <div className="w-full h-full bg-slate-900 flex flex-col items-center justify-center text-slate-600 relative">
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
                  <span className="absolute bottom-2 left-2 bg-rose-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                    {Math.round(v.confidence * 100)}%
                  </span>
                </div>
              </button>
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
