import { create } from 'zustand';

export interface UploadQueueItem {
  id: string;
  fileName: string;
  fileSize: number;
  progress: number; // 0 - 100
  status: 'uploading' | 'completed' | 'failed';
  error?: string;
  // An upload is a single multipart request: it can be aborted, but not resumed.
  request?: XMLHttpRequest;
}

interface UploadQueueState {
  items: UploadQueueItem[];
  addUpload: (id: string, name: string, size: number, request: XMLHttpRequest) => void;
  updateProgress: (id: string, progress: number) => void;
  setStatus: (id: string, status: UploadQueueItem['status'], error?: string) => void;
  cancelUpload: (id: string) => void;
  clearCompleted: () => void;
}

export const useUploadStore = create<UploadQueueState>((set, get) => ({
  items: [],
  addUpload: (id, name, size, request) =>
    set((state) => ({
      items: [
        ...state.items.filter((item) => item.id !== id),
        { id, fileName: name, fileSize: size, progress: 0, status: 'uploading', request },
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
  cancelUpload: (id) => {
    const item = get().items.find((i) => i.id === id);
    if (item && item.status === 'uploading') {
      item.request?.abort();
      set((state) => ({
        items: state.items.filter((i) => i.id !== id),
      }));
    }
  },
  clearCompleted: () =>
    set((state) => ({
      items: state.items.filter((item) => item.status !== 'completed'),
    })),
}));
