'use client';

import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { useAuthContext } from '../app/providers';
import { useTranslations } from 'next-intl';
import { Check, X, ShieldAlert } from 'lucide-react';
import { ViolationOverlay } from './VideoPlayerWithOverlay';
import { toast } from 'sonner';

interface ViolationReviewProps {
  violation: ViolationOverlay | null;
}

type Reviewable = ViolationOverlay & { reviewed?: boolean; verdict?: string | null };

export default function ViolationReview({ violation }: ViolationReviewProps) {
  const t = useTranslations('results');
  const { accessToken } = useAuthContext();
  const queryClient = useQueryClient();

  const reviewMutation = useMutation({
    mutationFn: async ({ id, isFlagged }: { id: string; isFlagged: boolean }) => {
      return apiClient(`/api/v1/violations/${id}`, {
        method: 'PATCH',
        token: accessToken,
        body: JSON.stringify({ isFlagged }),
      });
    },
    onSuccess: (_, variables) => {
      toast.success(
        variables.isFlagged ? 'Đã đánh dấu là nhận diện sai' : 'Đã phê duyệt vi phạm'
      );
      // Refresh both the results gallery and the dashboard counts.
      queryClient.invalidateQueries({ queryKey: ['violations'] });
    },
    onError: () => {
      toast.error('Gặp lỗi khi xử lý phê duyệt.');
    },
  });

  if (!violation) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex items-center justify-center text-slate-500 text-sm h-full min-h-[300px] text-center">
        Chọn một ảnh vi phạm trong thư viện để phê duyệt.
      </div>
    );
  }

  const cropUrl = violation.image_url || violation.imageUrl;
  const reviewed = (violation as Reviewable).reviewed;
  const verdict = (violation as Reviewable).verdict;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4 h-full">
      <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5 pb-2 border-b border-slate-800">
        <ShieldAlert className="w-4 h-4 text-rose-500" />
        Phê duyệt vi phạm
      </h4>

      {/* Enlarged crop of the selected violation */}
      <div className="rounded-lg overflow-hidden bg-slate-950 border border-slate-800 aspect-video flex items-center justify-center">
        {cropUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={cropUrl} alt="Vi phạm được chọn" className="w-full h-full object-contain" />
        ) : (
          <span className="text-slate-600 text-sm">Không có ảnh</span>
        )}
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">
          Độ tin cậy mô hình:{' '}
          <span className="font-semibold text-slate-200">
            {Math.round(violation.confidence * 100)}%
          </span>
        </span>
        {reviewed && (
          <span
            className={`px-2 py-0.5 rounded-full font-semibold border ${
              verdict === 'false positive'
                ? 'bg-rose-950/40 text-rose-400 border-rose-900/50'
                : 'bg-emerald-950/40 text-emerald-400 border-emerald-900/50'
            }`}
          >
            {verdict === 'false positive' ? 'Đã đánh dấu sai' : 'Đã phê duyệt'}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3 pt-2">
        <button
          onClick={() => reviewMutation.mutate({ id: violation.id, isFlagged: false })}
          disabled={reviewMutation.isPending}
          className="flex-1 flex justify-center items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm py-2 rounded-lg transition cursor-pointer"
        >
          <Check className="w-4 h-4" />
          {t('approve')}
        </button>
        <button
          onClick={() => reviewMutation.mutate({ id: violation.id, isFlagged: true })}
          disabled={reviewMutation.isPending}
          className="flex-1 flex justify-center items-center gap-1.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-semibold text-sm py-2 rounded-lg transition cursor-pointer"
        >
          <X className="w-4 h-4" />
          {t('dismiss')}
        </button>
      </div>
    </div>
  );
}
