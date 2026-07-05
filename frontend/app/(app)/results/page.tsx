'use client';

import React, { useState, useRef, use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useFilterStore } from '../../../store/useFilterStore';
import { useAuthContext } from '../../providers';
import { apiClient } from '../../../services/apiClient';
import VideoPlayerWithOverlay, { ViolationOverlay } from '../../../components/VideoPlayerWithOverlay';
import ViolationTimeline from '../../../components/ViolationTimeline';
import EvidenceGallery from '../../../components/EvidenceGallery';
import ViolationReview from '../../../components/ViolationReview';
import { useTranslations } from 'next-intl';
import { Sliders, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface ResultsPageProps {
  searchParams: Promise<{ video_id?: string }>;
}

export default function ResultsPage({ searchParams }: ResultsPageProps) {
  const { video_id } = use(searchParams);
  const t = useTranslations('results');
  const { accessToken } = useAuthContext();
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const confidenceThreshold = useFilterStore((state) => state.confidenceThreshold);
  const setConfidenceThreshold = useFilterStore((state) => state.setConfidenceThreshold);

  const [currentTime, setCurrentTime] = useState(0);

  // Fetch video details
  const { data: videoData } = useQuery({
    queryKey: ['video', video_id],
    queryFn: async () => {
      if (!video_id) return null;
      try {
        return await apiClient(`/api/v1/videos/${video_id}`, { token: accessToken });
      } catch (err) {
        console.warn('Backend video lookup failed, returning local debugging file path', err);
        return {
          id: video_id,
          filename: 'sample_traffic_feed.mp4',
          storagePath: 'https://www.w3schools.com/html/mov_bbb.mp4', // public fallback MP4 video
        };
      }
    },
    enabled: !!video_id,
  });

  // Fetch violations listing for the video
  const { data: violationsData } = useQuery({
    queryKey: ['violations', video_id],
    queryFn: async () => {
      if (!video_id) return [];
      try {
        const response = await apiClient(`/api/v1/violations?video_id=${video_id}`, { token: accessToken });
        return response.items || [];
      } catch (err) {
        console.warn('Backend violations call failed, using mock telemetry list', err);
        return [
          {
            id: 'v1',
            timestamp: 2.5,
            bbox: [100, 150, 250, 350],
            confidence: 0.88,
            label: 'non-helmet',
            isFlagged: false,
          },
          {
            id: 'v2',
            timestamp: 6.2,
            bbox: [400, 200, 550, 420],
            confidence: 0.94,
            label: 'helmet',
            isFlagged: false,
          },
          {
            id: 'v3',
            timestamp: 8.5,
            bbox: [200, 180, 320, 390],
            confidence: 0.45,
            label: 'non-helmet',
            isFlagged: false,
          },
        ] as ViolationOverlay[];
      }
    },
    enabled: !!video_id,
  });

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleConfidenceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfidenceThreshold(parseFloat(e.target.value));
  };

  const violations = (violationsData || []) as ViolationOverlay[];

  return (
    <div className="flex flex-col space-y-6 p-6 text-white max-w-7xl mx-auto">
      {/* Header bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/upload"
            className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {videoData?.filename || 'Processing Results'}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">Mã tài nguyên: {video_id}</p>
          </div>
        </div>

        {/* Global Confidence Threshold Control */}
        <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl shadow-md">
          <Sliders className="w-4 h-4 text-sky-400" />
          <span className="text-xs font-semibold text-slate-300">{t('confidenceSlider')}:</span>
          <input
            type="range"
            min="0.0"
            max="1.0"
            step="0.05"
            value={confidenceThreshold}
            onChange={handleConfidenceChange}
            className="w-32 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
          />
          <span className="text-xs font-mono font-bold text-sky-400 w-8 text-right">
            {Math.round(confidenceThreshold * 100)}%
          </span>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Video player and evidence gallery */}
        <div className="lg:col-span-2 space-y-6">
          <VideoPlayerWithOverlay
            src={videoData?.storagePath || ''}
            violations={violations}
            onTimeUpdate={setCurrentTime}
            videoRef={videoRef}
          />
          <EvidenceGallery
            violations={violations}
            onSelectCrop={handleSeek}
          />
        </div>

        {/* Right column: Timeline list and quick review triggers */}
        <div className="flex flex-col gap-6">
          <div className="flex-1">
            <ViolationTimeline
              violations={violations}
              currentTime={currentTime}
              onSeek={handleSeek}
            />
          </div>
          <ViolationReview
            violations={violations}
            currentTime={currentTime}
          />
        </div>
      </div>
    </div>
  );
}
