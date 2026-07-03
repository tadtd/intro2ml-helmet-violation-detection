interface RequestOptions extends RequestInit {
  token?: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function apiClient(path: string, options: RequestOptions = {}): Promise<any> {
  const url = `${API_BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});

  // Append in-memory access token if available
  if (options.token) {
    headers.set('Authorization', `Bearer ${options.token}`);
  }

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  let response = await fetch(url, config);

  // If 401 Unauthorized, perform silent refresh
  if (response.status === 401 && path !== '/api/v1/auth/refresh' && path !== '/api/v1/auth/login') {
    try {
      // 1. Request new access token (httpOnly cookie sent automatically)
      const refreshResponse = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
      });

      if (refreshResponse.ok) {
        const data = await refreshResponse.json();
        const newAccessToken = data.accessToken;

        // Update authorization header and replay request
        headers.set('Authorization', `Bearer ${newAccessToken}`);
        response = await fetch(url, { ...options, headers });

        // Broadcaster to update in-memory client context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth-token-refresh', { detail: newAccessToken }));
        }
      } else {
        // Refresh failed, trigger logout
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth-session-expired'));
        }
      }
    } catch {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth-session-expired'));
      }
    }
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'API request failed');
  }

  // Handle empty responses
  if (response.status === 204) {
    return null;
  }

  return response.json();
}
