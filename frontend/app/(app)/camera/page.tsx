'use client';

import React, { useRef, useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Camera, Radio, AlertCircle } from 'lucide-react';

interface DetectionBox {
  track_id: number;
  class: string;
  bbox: [number, number, number, number];
  conf: number;
  violation: boolean;
}

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function CameraPage() {
  const t = useTranslations('common');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [violationCount, setViolationCount] = useState(0);

  // Access the webcam stream when the component loads
  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing webcam:", err);
        setErrorMsg("Không thể truy cập camera (Webcam Error)");
      }
    }
    startCamera();

    const currentVideo = videoRef.current;
    return () => {
      if (currentVideo?.srcObject) {
        const tracks = (currentVideo.srcObject as MediaStream).getTracks();
        tracks.forEach((track) => track.stop());
      }
    };
  }, []);

  const connectStream = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    setErrorMsg(null);

    const wsUrl = apiBaseUrl.replace(/^http/, "ws");
    try {
      const socket = new WebSocket(`${wsUrl}/ws/camera`);
      wsRef.current = socket;

      socket.onopen = () => {
        // Protocol handshake - send JWT text token first
        socket.send("dummy_jwt_token_for_now");
      };

      socket.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.status === "authenticated") {
            setStatus('connected');
            startCaptureLoop();
            return;
          }

          if (data.violation_count !== undefined) {
            setViolationCount(data.violation_count);
          }
          if (data.boxes) {
            drawDetections(data.boxes);
          }
        } catch {
          // Ignore non-json messages or errors
        }
      };

      socket.onclose = (event) => {
        if (event.code === 4401) {
          setErrorMsg("Phiên kết nối hết hạn (Session Expired)");
        }
        setStatus('disconnected');
      };

      socket.onerror = (err) => {
        console.error('WS stream error:', err);
        setErrorMsg('Không thể thiết lập kết nối tới WebSocket.');
        setStatus('disconnected');
      };
    } catch {
      setErrorMsg('Gặp lỗi khi tạo kết nối luồng.');
      setStatus('disconnected');
    }
  };

  const disconnectStream = () => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('disconnected');

    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  async function startCaptureLoop() {
    const offscreenCanvas = document.createElement("canvas");
    offscreenCanvas.width = 640;
    offscreenCanvas.height = 480;
    const ctx = offscreenCanvas.getContext("2d");

    const captureFrame = async () => {
      if (!videoRef.current || !ctx || wsRef.current?.readyState !== WebSocket.OPEN) {
        return;
      }
      
      ctx.drawImage(videoRef.current, 0, 0, 640, 480);
      
      offscreenCanvas.toBlob(
        (blob) => {
          if (blob && wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(blob);
          }
        },
        "image/jpeg",
        0.7
      );

      setTimeout(captureFrame, 100);
    };

    captureFrame();
  }

  function drawDetections(boxes: DetectionBox[]) {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaleX = canvas.clientWidth / 640;
    const scaleY = canvas.clientHeight / 480;

    boxes.forEach((det) => {
      const isViolation = det.violation;
      const color = isViolation ? "red" : "green";
      
      const rawX1 = det.bbox[0];
      const rawY1 = det.bbox[1];
      const rawX2 = det.bbox[2];
      const rawY2 = det.bbox[3];

      const x = rawX1 * scaleX;
      const y = rawY1 * scaleY;
      const width = (rawX2 - rawX1) * scaleX;
      const height = (rawY2 - rawY1) * scaleY;

      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, width, height);

      ctx.fillStyle = color;
      ctx.font = "16px Arial";
      const label = `${det.class} (ID: ${det.track_id})`;
      ctx.fillText(label, x, y > 20 ? y - 5 : 20);
    });
  }

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
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="absolute inset-0 w-full h-full object-cover"
            />
            <canvas
              ref={canvasRef}
              width={640}
              height={480}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            />
            
            {status !== 'connected' && (
              <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center space-y-4 p-4 text-center z-10">
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
            Bảng điều khiển
          </h3>

          <div className="space-y-3">
             <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-4">
               <p className="text-xs text-slate-400 mb-1">Số vi phạm phiên này:</p>
               <p className="text-2xl font-bold text-rose-500">{violationCount}</p>
             </div>
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
