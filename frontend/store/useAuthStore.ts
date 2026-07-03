import { create } from 'zustand';

export interface UserSession {
  userId: string;
  fullName: string;
  role: 'admin' | 'operator';
}

interface AuthState {
  session: UserSession | null;
  isAuthenticated: boolean;
  login: (session: UserSession) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  isAuthenticated: false,
  login: (session) => set({ session, isAuthenticated: true }),
  logout: () => set({ session: null, isAuthenticated: false }),
}));
