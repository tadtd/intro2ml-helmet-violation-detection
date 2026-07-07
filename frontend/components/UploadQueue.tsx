'use client';

import React from 'react';
import { useUploadStore } from '../store/useUploadStore';
import { useTranslations } from 'next-intl';
import { Play, Pause, CheckCircle, AlertCircle } from 'lucide-react';

export default function UploadQueue() {
  const t = useTranslations('upload');
  const items = useUploadStore((state) => state.items);
  const pauseUpload = useUploadStore((state) => state.pauseUpload);
  const resumeUpload = useUploadStore((state) => state.resumeUpload);
  const clearCompleted = useUploadStore((state) => state.clearCompleted);

  if (items.length === 0) return null;

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4 max-w-2xl w-full">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="text-lg font-semibold text-white">{t('queueTitle')}</h3>
        <button
          onClick={clearCompleted}
          className="text-xs text-rose-400 hover:text-rose-300 font-medium transition cursor-pointer"
        >
          {t('cancel')}
        </button>
      </div>

      <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex flex-col bg-slate-950/50 border border-slate-800/80 rounded-lg p-4 space-y-2 hover:border-slate-700 transition"
          >
            <div className="flex justify-between items-start gap-4">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-200 truncate">{item.fileName}</p>
                <p className="text-xs text-slate-500">{formatSize(item.fileSize)}</p>
              </div>

              <div className="flex items-center gap-2">
                {item.status === 'uploading' && (
                  <button
                    onClick={() => pauseUpload(item.id)}
                    className="p-1.5 hover:bg-slate-800 rounded-full text-amber-400 transition cursor-pointer"
                    title={t('pause')}
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                )}
                {item.status === 'paused' && (
                  <button
                    onClick={() => resumeUpload(item.id)}
                    className="p-1.5 hover:bg-slate-800 rounded-full text-emerald-400 transition cursor-pointer"
                    title={t('resume')}
                  >
                    <Play className="w-4 h-4" />
                  </button>
                )}
                {item.status === 'completed' && (
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                )}
                {item.status === 'failed' && (
                  <div className="flex items-center gap-1 text-rose-500" title={item.error}>
                    <AlertCircle className="w-5 h-5" />
                  </div>
                )}
              </div>
            </div>

            {item.status !== 'completed' && item.status !== 'failed' && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-400">
                  <span>{item.status === 'paused' ? 'Paused' : 'Uploading...'}</span>
                  <span>{Math.round(item.progress)}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-sky-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              </div>
            )}

            {item.error && (
              <p className="text-xs text-rose-500 font-medium truncate">{item.error}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
