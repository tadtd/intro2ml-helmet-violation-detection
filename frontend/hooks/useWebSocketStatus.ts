'use client';

import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

export function useWebSocketStatus() {
  const [status, setStatus] = useState<'connected' | 'disconnected'>('disconnected');
  const queryClient = useQueryClient();

  useEffect(() => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/status`;
    let socket: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          setStatus('connected');
          console.log('WS status listener connected.');
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.event === 'job_status_update') {
              queryClient.setQueryData(['jobs'], (oldData: unknown) => {
                const list = (oldData as Array<{ jobId: string; status: string; completedAt?: string; fileName?: string }>) || [];
                const updated = list.map((job) => 
                  job.jobId === data.jobId ? { ...job, status: data.status, completedAt: data.completedAt } : job
                );
                // If it's a new job that wasn't in the list
                if (!updated.some((j) => j.jobId === data.jobId)) {
                  updated.unshift(data);
                }
                return updated;
              });

              // Trigger toast notification
              if (data.status === 'done') {
                toast.success(`Xử lý video ${data.fileName} hoàn thành!`);
              } else if (data.status === 'failed') {
                toast.error(`Xử lý video ${data.fileName} thất bại: ${data.error || 'Lỗi không xác định'}`);
              }
            } else if (data.event === 'new_violation_alert') {
              // Alert push notification
              toast.info(`Phát hiện vi phạm mới! Nhãn: ${data.label} (${Math.round(data.confidence * 100)}%)`);
              queryClient.invalidateQueries({ queryKey: ['violations'] });
            }
          } catch (e) {
            console.error('Error parsing WS status payload:', e);
          }
        };

        socket.onclose = () => {
          setStatus('disconnected');
          console.log('WS status closed, scheduling reconnect...');
          reconnectTimeout = setTimeout(connect, 5000); // retry connect in 5s
        };

        socket.onerror = (err) => {
          console.error('WS status socket encountered error:', err);
          socket?.close();
        };
      } catch (err) {
        console.error('WS connection failed:', err);
        setStatus('disconnected');
        reconnectTimeout = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      if (socket) {
        socket.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [queryClient]);

  return status;
}
