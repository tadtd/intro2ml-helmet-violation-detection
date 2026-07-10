'use client';

import React, { useRef, useEffect } from 'react';
import { useFilterStore } from '../store/useFilterStore';

export interface ViolationOverlay {
  id: string;
  timestamp: number; // in seconds
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number;
  label: 'non-helmet' | 'helmet' | 'motorbike';
  isFlagged: boolean;
  image_url?: string | null;
  imageUrl?: string | null;
}

interface VideoPlayerWithOverlayProps {
  src?: string | null;
  violations: ViolationOverlay[];
  onTimeUpdate?: (time: number) => void;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
}

export default function VideoPlayerWithOverlay({
  src,
  violations,
  onTimeUpdate,
  videoRef: externalVideoRef,
}: VideoPlayerWithOverlayProps) {
  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const videoRef = externalVideoRef || localVideoRef;
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const requestRef = useRef<number | null>(null);

  const confidenceThreshold = useFilterStore((state) => state.confidenceThreshold);

  // Update canvas size to match the video bounding client rect
  const updateCanvasSize = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      const rect = video.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    }
  };

  useEffect(() => {
    window.addEventListener('resize', updateCanvasSize);
    return () => window.removeEventListener('resize', updateCanvasSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const drawOverlays = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const currentTime = video.currentTime;
    const originalWidth = video.videoWidth || 1920; // default fallback
    const originalHeight = video.videoHeight || 1080;

    const scaleX = canvas.width / originalWidth;
    const scaleY = canvas.height / originalHeight;

    // Filter violations matching current timestamp (+/- 150ms window) and confidence threshold
    const activeOverlays = violations.filter((v) => {
      const timeDiff = Math.abs(v.timestamp - currentTime);
      return timeDiff <= 0.15 && v.confidence >= confidenceThreshold;
    });

    activeOverlays.forEach((overlay) => {
      const [x1, y1, x2, y2] = overlay.bbox;
      const x = x1 * scaleX;
      const y = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      // Color coding per labels
      let strokeColor = '#3b82f6'; // blue for motorbike
      let labelText = `Motorbike (${Math.round(overlay.confidence * 100)}%)`;

      if (overlay.label === 'non-helmet') {
        strokeColor = '#ef4444'; // red for non-helmet
        labelText = `NO HELMET (${Math.round(overlay.confidence * 100)}%)`;
      } else if (overlay.label === 'helmet') {
        strokeColor = '#10b981'; // green for helmet
        labelText = `Helmet (${Math.round(overlay.confidence * 100)}%)`;
      }

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(x, y, width, height);

      // Label background box
      ctx.fillStyle = strokeColor;
      ctx.font = 'bold 11px sans-serif';
      const textWidth = ctx.measureText(labelText).width;
      ctx.fillRect(x, y - 18, textWidth + 10, 18);

      // Label text
      ctx.fillStyle = '#ffffff';
      ctx.fillText(labelText, x + 5, y - 5);
    });

    if (onTimeUpdate) {
      onTimeUpdate(currentTime);
    }
  };

  const renderLoop = () => {
    drawOverlays();
    requestRef.current = requestAnimationFrame(renderLoop);
  };

  const handlePlay = () => {
    updateCanvasSize();
    requestRef.current = requestAnimationFrame(renderLoop);
  };

  const handlePause = () => {
    if (requestRef.current) {
      cancelAnimationFrame(requestRef.current);
      requestRef.current = null;
    }
    drawOverlays(); // final render frame draw on pause
  };

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      // Trigger canvas size update when video loads metadata
      video.addEventListener('loadedmetadata', updateCanvasSize);
      video.addEventListener('play', handlePlay);
      video.addEventListener('pause', handlePause);
      video.addEventListener('seeked', drawOverlays);

      return () => {
        video.removeEventListener('loadedmetadata', updateCanvasSize);
        video.removeEventListener('play', handlePlay);
        video.removeEventListener('pause', handlePause);
        video.removeEventListener('seeked', drawOverlays);
        if (requestRef.current) {
          cancelAnimationFrame(requestRef.current);
        }
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [violations, confidenceThreshold]);

  // Re-draw overlays when the slider triggers changes while paused
  useEffect(() => {
    drawOverlays();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [confidenceThreshold, violations]);

  if (!src) {
    return (
      <div className="relative w-full rounded-xl overflow-hidden bg-black shadow-2xl aspect-video border border-slate-800 flex items-center justify-center text-slate-500 text-sm">
        Video source is not available yet.
      </div>
    );
  }

  const videoSrc = src;

  return (
    <div className="relative w-full rounded-xl overflow-hidden bg-black shadow-2xl aspect-video border border-slate-800">
      <video
        ref={videoRef}
        src={videoSrc}
        controls
        className="w-full h-full object-contain"
        crossOrigin="anonymous"
        onLoadedData={updateCanvasSize}
      />
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}
