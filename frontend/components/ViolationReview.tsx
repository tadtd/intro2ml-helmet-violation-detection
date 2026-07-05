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
  violations: ViolationOverlay[];
  currentTime: number;
}

export default function ViolationReview({ violations, currentTime }: ViolationReviewProps) {
  const t = useTranslations('results');
  const { accessToken } = useAuthContext();
  const queryClient = useQueryClient();

  // Find violation nearest to currentTime (for fast context flagging)
  const activeViolation = violations.find(
    (v) => Math.abs(v.timestamp - currentTime) <= 1.5 && v.label === 'non-helmet'
  );

  const reviewMutation = useMutation({
    mutationFn: async ({ id, isFlagged }: { id: string; isFlagged: boolean }) => {
      try {
        return await apiClient(`/api/v1/violations/${id}`, {
          method: 'PATCH',
          token: accessToken,
          body: JSON.stringify({ isFlagged }),
        });
      } catch (err) {
        // Fallback for offline development / mocking review
        console.warn('Backend patch failed, triggering client fallback state', err);
        return { id, isFlagged };
      }
    },
    onSuccess: (_, variables) => {
      toast.success(
        variables.isFlagged ? 'Đã đánh dấu lỗi phân tích' : 'Đã duyệt vi phạm thành công'
      );
      // Invalidate query to trigger refresh
      queryClient.invalidateQueries({ queryKey: ['violations'] });
    },
    onError: (err) => {
      console.error(err);
      toast.error('Gặp lỗi khi xử lý phê duyệt.');
    },
  });

  if (!activeViolation) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex items-center justify-center text-slate-500 text-sm h-full min-h-[140px]">
        Không có vi phạm nào ở khung hình hiện tại cần phê duyệt.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4 h-full min-h-[140px] flex flex-col justify-between">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-500" />
            Phê duyệt vi phạm tại {Math.round(activeViolation.timestamp)}s
          </h4>
          <p className="text-xs text-slate-400">
            Độ tin cậy mô hình: {Math.round(activeViolation.confidence * 100)}%
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 mt-4">
        <button
          onClick={() =>
            reviewMutation.mutate({ id: activeViolation.id, isFlagged: false })
          }
          disabled={reviewMutation.isPending}
          className="flex-1 flex justify-center items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm py-2 rounded-lg transition cursor-pointer"
        >
          <Check className="w-4 h-4" />
          {t('approve')}
        </button>
        <button
          onClick={() =>
            reviewMutation.mutate({ id: activeViolation.id, isFlagged: true })
          }
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
