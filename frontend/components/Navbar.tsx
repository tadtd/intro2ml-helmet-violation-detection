'use client';

import React from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { useAuthContext } from '../app/providers';
import { useTranslations } from 'next-intl';
import { LogOut, Globe, Shield, Video, UploadCloud, LayoutDashboard } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useLocale } from 'next-intl';

export default function Navbar() {
  const t = useTranslations('common');
  const session = useAuthStore((state) => state.session);
  const logout = useAuthStore((state) => state.logout);
  const { setAccessToken } = useAuthContext();
  const router = useRouter();
  const locale = useLocale();

  const handleLogout = () => {
    // 1. Clear Zustand session
    logout();
    // 2. Clear in-memory token
    setAccessToken(null);
    // 3. Expire cookies
    document.cookie = 'session_active=; Max-Age=0; path=/';
    document.cookie = 'user_role=; Max-Age=0; path=/';
    // 4. Redirect
    router.push('/login');
  };

  const toggleLanguage = () => {
    const nextLocale = locale === 'vi' ? 'en' : 'vi';
    document.cookie = `NEXT_LOCALE=${nextLocale}; path=/; max-age=31536000; SameSite=Strict`;
    window.location.reload();
  };

  const navItems = [
    { href: '/dashboard', label: t('dashboard'), icon: LayoutDashboard },
    { href: '/upload', label: t('upload'), icon: UploadCloud },
    { href: '/camera', label: t('camera'), icon: Video },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900 sticky top-0 z-50">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link className="font-bold text-lg text-white flex items-center gap-2" href="/dashboard">
          <Shield className="w-5 h-5 text-sky-400" />
          <span>{t('title')}</span>
        </Link>
        
        <div className="flex items-center gap-6">
          <nav className="flex gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  className="rounded-md px-3 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-1.5 transition"
                  href={item.href}
                  key={item.href}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="h-4 w-px bg-slate-800" />

          <div className="flex items-center gap-4">
            {/* Language Switch */}
            <button
              onClick={toggleLanguage}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-300 hover:text-white transition flex items-center gap-1.5 cursor-pointer text-xs font-bold text-sky-400"
            >
              <Globe className="w-4 h-4" />
              <span>{locale === 'vi' ? 'VI' : 'EN'}</span>
            </button>

            {/* Session profile and Logout */}
            {session && (
              <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-white">{session.fullName}</p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wider">{session.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 hover:bg-slate-800 rounded-lg text-slate-300 hover:text-white transition cursor-pointer"
                  title={t('logout')}
                >
                  <LogOut className="w-4.5 h-4.5 text-rose-500" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
