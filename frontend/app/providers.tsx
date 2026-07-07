'use client';

import React, { createContext, useContext, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NextIntlClientProvider } from 'next-intl';

interface AuthContextType {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}

import { AbstractIntlMessages } from 'next-intl';

export default function Providers({
  children,
  messages,
  locale,
}: {
  children: React.ReactNode;
  messages: AbstractIntlMessages;
  locale: string;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );
  
  const [accessToken, setAccessToken] = useState<string | null>(null);

  React.useEffect(() => {
    const handleRefresh = (e: Event) => {
      const customEvent = e as CustomEvent<string>;
      setAccessToken(customEvent.detail);
    };
    const handleExpired = () => {
      setAccessToken(null);
      // Clear session indicator cookies
      document.cookie = 'session_active=; Max-Age=0; path=/';
      document.cookie = 'user_role=; Max-Age=0; path=/';
      window.location.href = '/login';
    };

    window.addEventListener('auth-token-refresh', handleRefresh);
    window.addEventListener('auth-session-expired', handleExpired);

    return () => {
      window.removeEventListener('auth-token-refresh', handleRefresh);
      window.removeEventListener('auth-session-expired', handleExpired);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={{ accessToken, setAccessToken }}>
        <NextIntlClientProvider locale={locale} messages={messages} timeZone="Asia/Ho_Chi_Minh">
          {children}
        </NextIntlClientProvider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}
