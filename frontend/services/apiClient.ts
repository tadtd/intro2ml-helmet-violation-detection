interface RequestOptions extends RequestInit {
  token?: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

const buildUrl = (path: string) => {
  if (/^https?:\/\//.test(path)) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
};

const parseErrorResponse = async (response: Response) => {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const body = await response.json().catch(() => null);
    return body?.detail || body?.message || response.statusText;
  }

  return response.statusText || 'API request failed';
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function apiClient(path: string, options: RequestOptions = {}): Promise<any> {
  const url = buildUrl(path);
  const headers = new Headers(options.headers || {});

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

  let response: Response;
  try {
    response = await fetch(url, config);
  } catch (error) {
    throw new Error(
      `Cannot reach backend API at ${url}. Make sure the backend/API gateway is running and NEXT_PUBLIC_API_URL is correct.`,
      { cause: error },
    );
  }

  if (response.status === 401 && typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('auth-session-expired'));
  }

  if (!response.ok) {
    throw new Error(await parseErrorResponse(response));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}