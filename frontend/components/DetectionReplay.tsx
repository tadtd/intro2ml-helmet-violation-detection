'use client';

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Play, RotateCcw, ShieldAlert, AlertCircle, Square } from 'lucide-react';

interface DetectionReplayProps {
  src: string | null;
  model?: string;
}

// Replays a processed video through the realtime detection service, which draws
// the detection boxes server-side. This reuses the live-stream pipeline, so the
// results view shows boxes without needing per-frame boxes stored in the database.
export default function DetectionReplay({ src, model = 'yolo' }: DetectionReplayProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'playing' | 'ended'>('idle');
  const [stats, setStats] = useState({ detections: 0, violations: 0 });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const stop = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.onclose = null;
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const stopPlayback = useCallback(() => {
    stop();
    setStatus('ended');
  }, [stop]);

  const start = useCallback(() => {
    if (!src) return;
    stop();
    setErrorMsg(null);
    setStats({ detections: 0, violations: 0 });
    setStatus('connecting');

    const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const url = `${wsBase}/ws/camera?src=${encodeURIComponent(src)}&model=${model}`;
    const socket = new WebSocket(url);
    socket.binaryType = 'arraybuffer';
    socketRef.current = socket;

    socket.onopen = () => setStatus('playing');

    socket.onmessage = (event) => {
      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'stats') setStats({ detections: msg.detections, violations: msg.violations });
          else if (msg.type === 'error') {
            setErrorMsg(msg.message);
            setStatus('ended');
          }
        } catch {
          /* ignore */
        }
        return;
      }
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const blob = new Blob([event.data as ArrayBuffer], { type: 'image/jpeg' });
      const objectUrl = URL.createObjectURL(blob);
      const img = new Image();
      img.onload = () => {
        if (canvas.width !== img.width) canvas.width = img.width;
        if (canvas.height !== img.height) canvas.height = img.height;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(objectUrl);
      };
      img.src = objectUrl;
    };

    socket.onerror = () => {
      setErrorMsg('Không thể kết nối luồng phát hiện.');
      setStatus('ended');
    };
    socket.onclose = () => setStatus((s) => (s === 'playing' ? 'ended' : s));
  }, [src, model, stop]);

  useEffect(() => () => stop(), [stop]);

  return (
    <div className="space-y-3">
      <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl flex items-center justify-center">
        <canvas ref={canvasRef} width={1280} height={720} className="w-full h-full object-contain" />

        {status !== 'playing' && (
          <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center gap-4 p-4 text-center">
            <button
              onClick={start}
              disabled={!src || status === 'connecting'}
              className="flex items-center gap-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold text-sm py-2.5 px-5 rounded-lg transition cursor-pointer"
            >
              <Play className="w-4 h-4" />
              {status === 'connecting'
                ? 'Đang xử lý…'
                : status === 'ended'
                ? 'Xem lại với phát hiện AI'
                : 'Phát với phát hiện AI'}
            </button>
            <p className="text-[11px] text-slate-500 max-w-xs">
              Chạy lại video qua mô hình để vẽ hộp phát hiện theo thời gian thực.
            </p>
          </div>
        )}

        {status === 'playing' && (
          <>
            <div className="absolute top-3 left-3 flex items-center gap-2 bg-slate-950/70 px-3 py-1.5 rounded-lg text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" /> AI
            </div>
            <div className="absolute top-3 right-3 flex gap-2">
              <span className="bg-slate-950/70 px-3 py-1.5 rounded-lg text-xs font-semibold text-sky-300">
                {stats.detections} đối tượng
              </span>
              <span
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${
                  stats.violations > 0
                    ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                    : 'bg-slate-950/70 text-slate-300'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                {stats.violations} vi phạm
              </span>
            </div>
            <div className="absolute bottom-3 left-3 right-3 flex flex-col gap-2 rounded-lg bg-slate-950/75 border border-slate-800 px-3 py-2 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
              <p className="text-[11px] text-slate-400">
                Luồng AI được vẽ lên canvas. Dùng tab Video gốc để tua, tạm dừng hoặc xem bằng trình phát chuẩn.
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={stopPlayback}
                  className="flex items-center gap-1.5 rounded-md bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:bg-slate-700"
                >
                  <Square className="h-3.5 w-3.5" />
                  Dừng
                </button>
                <button
                  onClick={start}
                  className="flex items-center gap-1.5 rounded-md bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-sky-500"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Xem lại
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 p-3 bg-rose-950/20 border border-rose-900/40 text-rose-400 rounded-lg text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
