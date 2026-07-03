import { create } from 'zustand';

export interface DateRange {
  startDate: string; // ISO format
  endDate: string;   // ISO format
}

interface FilterState {
  confidenceThreshold: number; // 0.0 - 1.0 (defaults to 0.5)
  dateRange: DateRange;
  selectedModel: 'all' | 'yolo' | 'rtdetr' | 'fasterrcnn';
  selectedStatus: 'all' | 'pending' | 'approved' | 'dismissed';
  setConfidenceThreshold: (val: number) => void;
  setDateRange: (range: DateRange) => void;
  setSelectedModel: (model: FilterState['selectedModel']) => void;
  setSelectedStatus: (status: FilterState['selectedStatus']) => void;
  resetFilters: () => void;
}

const getDefaultDateRange = (): DateRange => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 7); // Default to last 7 days
  return {
    startDate: start.toISOString().split('T')[0] + 'T00:00:00.000Z',
    endDate: end.toISOString().split('T')[0] + 'T23:59:59.999Z',
  };
};

export const useFilterStore = create<FilterState>((set) => ({
  confidenceThreshold: 0.5,
  dateRange: getDefaultDateRange(),
  selectedModel: 'all',
  selectedStatus: 'all',
  setConfidenceThreshold: (val) => set({ confidenceThreshold: val }),
  setDateRange: (range) => set({ dateRange: range }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setSelectedStatus: (status) => set({ selectedStatus: status }),
  resetFilters: () =>
    set({
      confidenceThreshold: 0.5,
      dateRange: getDefaultDateRange(),
      selectedModel: 'all',
      selectedStatus: 'all',
    }),
}));
