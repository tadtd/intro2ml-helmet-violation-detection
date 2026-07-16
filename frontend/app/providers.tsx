'use client';

import React, { createContext, useContext, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NextIntlClientProvider } from 'next-intl';
import { AbstractIntlMessages } from 'next-intl';
import { useWebSocketStatus } from '../hooks/useWebSocketStatus';
import { createClient } from '../utils/supabase/client';
import { useAuthStore, UserSession } from '../store/useAuthStore';

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

function BackendRealtimeBridge() {
  useWebSocketStatus();
  return null;
}

const getCookieValue = (name: string) => {
  if (typeof document === 'undefined') return null;
  const match = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1] || '') : null;
};

const restoreAuthStoreSession = (session: {
  access_token?: string;
  user?: {
    id: string;
    email?: string;
    user_metadata?: Record<string, unknown>;
  };
} | null) => {
  const authStore = useAuthStore.getState();
  const user = session?.user;

  if (!session?.access_token || !user) {
    authStore.logout();
    return;
  }

  const metadata = user.user_metadata || {};
  const cookieRole = getCookieValue('user_role');
  const metadataRole = typeof metadata.role === 'string' ? metadata.role : null;
  const role = cookieRole === 'admin' || cookieRole === 'operator'
    ? cookieRole
    : metadataRole === 'admin' || metadataRole === 'operator'
      ? metadataRole
      : 'operator';
  const fullName = typeof metadata.full_name === 'string' && metadata.full_name
    ? metadata.full_name
    : user.email?.split('@')[0] || 'Operator';

  authStore.login({
    userId: user.id,
    fullName,
    role,
  } satisfies UserSession);
};

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
  const [isSessionRestored, setIsSessionRestored] = useState(false);

  // The token lives in memory only, so a page reload would otherwise drop it and
  // every API call would go out unauthenticated. Supabase persists the session
  // itself, so rehydrate from it on mount and follow later auth changes.
  React.useEffect(() => {
    const supabase = createClient();

    supabase.auth
      .getSession()
      .then(({ data }) => {
        setAccessToken(data.session?.access_token ?? null);
        restoreAuthStoreSession(data.session);
      })
      .finally(() => setIsSessionRestored(true));

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAccessToken(session?.access_token ?? null);
      restoreAuthStoreSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  React.useEffect(() => {
    const handleRefresh = (e: Event) => {
      const customEvent = e as CustomEvent<string>;
      setAccessToken(customEvent.detail);
    };
    const handleExpired = () => {
      setAccessToken(null);
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
          <BackendRealtimeBridge />
          {/* Pages fire authenticated queries on mount, so hold them back until the
              Supabase session has been restored. Rendering earlier would send the
              first request with no token and the 401 would log the user out. */}
          {isSessionRestored ? children : null}
        </NextIntlClientProvider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}
