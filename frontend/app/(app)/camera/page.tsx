'use client';

import React, { useRef, useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Camera, Radio, AlertCircle } from 'lucide-react';

export default function CameraPage() {
  const t = useTranslations('common');
  const socketRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedCamera, setSelectedCamera] = useState('cam-01');
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const cameras = [
    { id: 'cam-01', name: 'Ngã tư Trần Hưng Đạo - Nguyễn Văn Cừ' },
    { id: 'cam-02', name: 'Ngã tư Lê Hồng Phong - Nguyễn Thị Minh Khai' },
    { id: 'cam-03', name: 'Đường Ba Tháng Hai (Vòng xoay Dân Chủ)' },
  ];

  const connectStream = () => {
    disconnectStream();
    setStatus('connecting');
    setErrorMsg(null);

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
    const wsUrl = apiBaseUrl.replace(/^http/, 'ws');
    
    try {
      const socket = new WebSocket(`${wsUrl}/ws/camera?id=${selectedCamera}`);
      socket.binaryType = 'arraybuffer';
      socketRef.current = socket;

      socket.onopen = () => {
        setStatus('connected');
      };

      socket.onmessage = (event) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        try {
          let imageBlob: Blob;
          
          if (event.data instanceof ArrayBuffer) {
            // Binary frames payload
            imageBlob = new Blob([event.data], { type: 'image/jpeg' });
          } else {
            // JSON frames format payload e.g. base64 image data
            const data = JSON.parse(event.data);
            if (data.frameData) {
              const byteCharacters = atob(data.frameData);
              const byteNumbers = new Array(byteCharacters.length);
              for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
              }
              const byteArray = new Uint8Array(byteNumbers);
              imageBlob = new Blob([byteArray], { type: 'image/jpeg' });
            } else {
              return;
            }
          }

          const url = URL.createObjectURL(imageBlob);
          const img = new Image();
          img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);
          };
          img.src = url;
        } catch (e) {
          console.error('Error drawing frame to canvas:', e);
        }
      };

      socket.onclose = () => {
        setStatus('disconnected');
      };

      socket.onerror = (err) => {
        console.error('WS stream error:', err);
        setErrorMsg('Không thể thiết lập kết nối tới nguồn camera.');
        setStatus('disconnected');
      };
    } catch {
      setErrorMsg('Gặp lỗi khi tạo kết nối luồng.');
      setStatus('disconnected');
    }
  };

  const disconnectStream = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setStatus('disconnected');
    
    // Clear canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  useEffect(() => {
    return () => {
      disconnectStream();
    };
  }, []);

  return (
    <div className="flex flex-col space-y-6 p-6 text-white max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('camera')}</h1>
        <p className="text-sm text-slate-400 mt-2">
          Theo dõi trực tiếp luồng camera giao thông và phát hiện lỗi vi phạm thời gian thực.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl flex items-center justify-center">
            <canvas ref={canvasRef} width={640} height={360} className="w-full h-full object-contain" />
            
            {status !== 'connected' && (
              <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center space-y-4 p-4 text-center">
                <Camera className="w-12 h-12 text-slate-600 animate-pulse" />
                <p className="text-sm font-semibold text-slate-400">
                  {status === 'connecting' ? 'Đang kết nối luồng camera...' : 'Chưa có kết nối nguồn phát'}
                </p>
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
            Nguồn camera
          </h3>

          <div className="space-y-3">
            {cameras.map((cam) => (
              <button
                key={cam.id}
                onClick={() => {
                  setSelectedCamera(cam.id);
                  if (status === 'connected') {
                    // Reconnect on change
                    setTimeout(connectStream, 100);
                  }
                }}
                className={`w-full text-left p-3.5 rounded-lg border transition cursor-pointer text-xs font-semibold ${
                  selectedCamera === cam.id
                    ? 'bg-sky-950/40 border-sky-500 text-sky-300'
                    : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                {cam.name}
              </button>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center gap-3">
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
        </div>
      </div>
    </div>
  );
}
