'use client';

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Camera, Radio, AlertCircle, ShieldAlert } from 'lucide-react';

type Status = 'connected' | 'disconnected' | 'connecting';

// Detection sources served by the realtime stream service. The named ones map to
// demo clips on the server; "custom" accepts any RTSP / HLS / YouTube-live URL,
// which the backend resolves and runs the model over.
const DETECT_SOURCES = [
  { id: 'demo-violation', name: 'Demo — nhiều vi phạm (không mũ)' },
  { id: 'demo-traffic', name: 'Demo — đường phố (TP.HCM)' },
  { id: 'custom', name: 'Nguồn trực tiếp (RTSP / HLS / YouTube)…' },
];

const MODELS = [
  { id: 'yolo', name: 'YOLO' },
  { id: 'rtdetr', name: 'RT-DETR' },
  { id: 'fasterrcnn', name: 'Faster R-CNN' },
];

export default function CameraPage() {
  const t = useTranslations('common');
  const socketRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [source, setSource] = useState('demo-violation');
  const [customUrl, setCustomUrl] = useState('');
  const [model, setModel] = useState('yolo');
  const [status, setStatus] = useState<Status>('disconnected');
  const [stats, setStats] = useState({ detections: 0, violations: 0 });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const disconnectStream = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.onclose = null;
      socketRef.current.close();
      socketRef.current = null;
    }
    setStatus('disconnected');
    setStats({ detections: 0, violations: 0 });
    const canvas = canvasRef.current;
    if (canvas) canvas.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height);
  }, []);

  const connectStream = useCallback(() => {
    disconnectStream();
    setErrorMsg(null);

    const streamSource = source === 'custom' ? customUrl.trim() : source;
    if (source === 'custom' && !streamSource) {
      setErrorMsg('Vui lòng nhập địa chỉ luồng RTSP / HLS hoặc URL YouTube trực tiếp.');
      return;
    }

    setStatus('connecting');
    const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const url = `${wsBase}/ws/camera?id=${encodeURIComponent(streamSource)}&model=${model}`;

    try {
      const socket = new WebSocket(url);
      socket.binaryType = 'arraybuffer';
      socketRef.current = socket;

      socket.onopen = () => setStatus('connected');

      socket.onmessage = (event) => {
        // Text frames carry JSON stats/errors; binary frames carry JPEG images.
        if (typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'stats') {
              setStats({ detections: msg.detections, violations: msg.violations });
            } else if (msg.type === 'error') {
              setErrorMsg(msg.message);
              disconnectStream();
            }
          } catch {
            // ignore malformed text frame
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
        setErrorMsg('Không thể thiết lập kết nối tới luồng phát hiện.');
        setStatus('disconnected');
      };

      socket.onclose = () => setStatus('disconnected');
    } catch {
      setErrorMsg('Gặp lỗi khi tạo kết nối luồng.');
      setStatus('disconnected');
    }
  }, [source, customUrl, model, disconnectStream]);

  useEffect(() => () => disconnectStream(), [disconnectStream]);

  return (
    <div className="flex flex-col space-y-6 p-6 text-white max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('camera')}</h1>
        <p className="text-sm text-slate-400 mt-2">
          Phát hiện vi phạm mũ bảo hiểm theo thời gian thực trên luồng camera trực tiếp.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl flex items-center justify-center">
            <canvas ref={canvasRef} width={1280} height={720} className="w-full h-full object-contain" />

            {status !== 'connected' && (
              <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center space-y-4 p-4 text-center">
                <Camera className="w-12 h-12 text-slate-600 animate-pulse" />
                <p className="text-sm font-semibold text-slate-400">
                  {status === 'connecting' ? 'Đang kết nối luồng…' : 'Chưa có kết nối nguồn phát'}
                </p>
              </div>
            )}

            {status === 'connected' && (
              <div className="absolute top-3 left-3 flex items-center gap-2 bg-slate-950/70 px-3 py-1.5 rounded-lg text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" /> LIVE
              </div>
            )}

            {status === 'connected' && (
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
            )}
          </div>

          {errorMsg && (
            <div className="flex items-center gap-2 p-3.5 bg-rose-950/20 border border-rose-900/40 text-rose-400 rounded-lg text-xs">
              <AlertCircle className="w-4.5 h-4.5 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-5 h-fit">
          <h3 className="text-md font-semibold text-slate-200 border-b border-slate-800 pb-2 flex items-center gap-2">
            <Radio className="w-4.5 h-4.5 text-sky-400" />
            Nguồn phát
          </h3>

          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Chọn nguồn</label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              disabled={status === 'connected'}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-slate-200 text-sm focus:outline-none focus:border-sky-500 disabled:opacity-50"
            >
              {DETECT_SOURCES.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>

            {source === 'custom' && (
              <input
                type="text"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                disabled={status === 'connected'}
                placeholder="rtsp://…  ·  https://…/live.m3u8  ·  https://youtube.com/watch?v=…"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-slate-200 text-sm focus:outline-none focus:border-sky-500 disabled:opacity-50"
              />
            )}

            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Mô hình</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={status === 'connected'}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-slate-200 text-sm focus:outline-none focus:border-sky-500 disabled:opacity-50"
            >
              {MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>

          <div className="pt-4 border-t border-slate-800">
            {status === 'connected' ? (
              <button
                onClick={disconnectStream}
                className="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-2 rounded-lg transition text-xs cursor-pointer"
              >
                Ngắt kết nối
              </button>
            ) : (
              <button
                onClick={connectStream}
                disabled={status === 'connecting'}
                className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold py-2 rounded-lg transition text-xs cursor-pointer"
              >
                Kết nối phát trực tiếp
              </button>
            )}
          </div>

          <p className="text-[11px] leading-relaxed text-slate-500">
            Luồng được giải mã phía máy chủ, chạy qua mô hình ONNX và trả về khung hình đã gắn hộp
            phát hiện. Hỗ trợ RTSP, HLS và URL YouTube trực tiếp — có thể cắm vào camera giao thông
            thật khi có nguồn phát.
          </p>
        </div>
      </div>
    </div>
  );
}
