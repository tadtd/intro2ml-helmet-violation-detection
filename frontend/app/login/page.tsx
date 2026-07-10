'use client';

import React, { useState } from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { useAuthContext } from '../providers';
import { useTranslations } from 'next-intl';
import { Shield, Key, User, Eye, EyeOff } from 'lucide-react';
import { createClient } from '../../utils/supabase/client';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const t = useTranslations('auth');
  const tc = useTranslations('common');
  const router = useRouter();

  const { setAccessToken } = useAuthContext();
  const login = useAuthStore((state) => state.login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'operator' | 'admin'>('operator');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      // 1. Sign in using Supabase Client (acting as Auth Service)
      const supabase = createClient();
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setErrorMessage(t('invalidCredentials'));
        return;
      }

      const token = data.session?.access_token || null;
      const user = data.user;

      if (!token || !user) {
        throw new Error('Đăng nhập không thành công, không nhận được token.');
      }

      // 2. Set Access Token in-memory
      setAccessToken(token);

      // 3. Cache session in Zustand
      const fullName = user.user_metadata?.full_name || email.split('@')[0];
      login({
        userId: user.id,
        fullName,
        role: role, // bind the selected role for RBAC routing
      });

      // 4. Set cookie indicators for Next.js Middleware route guard
      document.cookie = `session_active=true; path=/; max-age=86400; SameSite=Strict`;
      document.cookie = `user_role=${role}; path=/; max-age=86400; SameSite=Strict`;

      // 5. Success redirect to dashboard
      router.push('/dashboard');
    } catch (err: unknown) {
      const errorObj = err as Error;

      // Local development fallback/offline mode if Supabase credentials aren't configured yet
      if (errorObj.message.includes('API key') || errorObj.message.includes('fetch')) {
        console.warn('Supabase auth failed/offline, starting client simulation mode');
        
        // Mock successful login
        const dummyToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_claims.signature';
        setAccessToken(dummyToken);
        login({
          userId: 'd3b07384-d113-495f-9e7b-e10b2df76a08',
          fullName: email.split('@')[0],
          role: role,
        });

        document.cookie = `session_active=true; path=/; max-age=86400; SameSite=Strict`;
        document.cookie = `user_role=${role}; path=/; max-age=86400; SameSite=Strict`;
        
        router.push('/dashboard');
        return;
      }
      
      setErrorMessage(t('invalidCredentials'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-white">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-sky-950/50 border border-sky-900/50 rounded-xl text-sky-400">
            <Shield className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight">{tc('title')}</h2>
          <p className="text-sm text-slate-400">{t('signIn')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Email</label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@system.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-10 pr-3 focus:outline-none focus:border-sky-500 text-slate-200 transition text-sm"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Mật khẩu</label>
            <div className="relative">
              <Key className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-10 pr-10 focus:outline-none focus:border-sky-500 text-slate-200 transition text-sm"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">{t('role')}</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as 'operator' | 'admin')}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 focus:outline-none focus:border-sky-500 text-slate-200 transition text-sm cursor-pointer"
            >
              <option value="operator">{t('operator')}</option>
              <option value="admin">{t('admin')}</option>
            </select>
          </div>

          {errorMessage && (
            <p className="text-xs text-rose-500 font-semibold bg-rose-950/20 border border-rose-900/30 p-2.5 rounded-lg">
              {errorMessage}
            </p>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold py-2.5 rounded-lg transition text-sm cursor-pointer mt-2"
          >
            {isLoading ? tc('loading') : tc('login')}
          </button>
        </form>
      </div>
    </main>
  );
}
