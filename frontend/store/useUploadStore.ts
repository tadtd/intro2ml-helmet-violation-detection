import { create } from 'zustand';
import { Upload } from 'tus-js-client';

export interface UploadQueueItem {
  id: string;
  fileName: string;
  fileSize: number;
  progress: number; // 0 - 100
  status: 'uploading' | 'paused' | 'completed' | 'failed';
  error?: string;
  tusInstance?: Upload;
}

interface UploadQueueState {
  items: UploadQueueItem[];
  addUpload: (id: string, name: string, size: number, tus: Upload) => void;
  updateProgress: (id: string, progress: number) => void;
  setStatus: (id: string, status: UploadQueueItem['status'], error?: string) => void;
  pauseUpload: (id: string) => void;
  resumeUpload: (id: string) => void;
  clearCompleted: () => void;
}

export const useUploadStore = create<UploadQueueState>((set, get) => ({
  items: [],
  addUpload: (id, name, size, tus) =>
    set((state) => ({
      items: [
        ...state.items.filter((item) => item.id !== id),
        { id, fileName: name, fileSize: size, progress: 0, status: 'uploading', tusInstance: tus },
      ],
    })),
  updateProgress: (id, progress) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, progress } : item
      ),
    })),
  setStatus: (id, status, error) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, status, error } : item
      ),
    })),
  pauseUpload: (id) => {
    const item = get().items.find((i) => i.id === id);
    if (item && item.tusInstance && item.status === 'uploading') {
      item.tusInstance.abort();
      set((state) => ({
        items: state.items.map((i) =>
          i.id === id ? { ...i, status: 'paused' as const } : i
        ),
      }));
    }
  },
  resumeUpload: (id) => {
    const item = get().items.find((i) => i.id === id);
    if (item && item.tusInstance && item.status === 'paused') {
      item.tusInstance.start();
      set((state) => ({
        items: state.items.map((i) =>
          i.id === id ? { ...i, status: 'uploading' as const } : i
        ),
      }));
    }
  },
  clearCompleted: () =>
    set((state) => ({
      items: state.items.filter((item) => item.status !== 'completed'),
    })),
}));
