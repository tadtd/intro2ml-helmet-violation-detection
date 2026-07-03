import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { updateSession } from "@/utils/supabase/middleware";

export async function proxy(request: NextRequest) {
  // 1. Perform Supabase session updates
  const response = await updateSession(request);

  const { pathname } = request.nextUrl;

  // Skip static assets, login/register routes
  if (
    pathname.startsWith('/_next') ||
    pathname.includes('/api/') ||
    pathname === '/login' ||
    pathname === '/register' ||
    pathname.includes('/favicon.ico')
  ) {
    return response;
  }

  // 2. Read cookie indicators (set on login)
  const hasSession = request.cookies.has('session_active');

  // 3. Redirect unauthenticated users
  if (!hasSession) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  // 4. Enforce role checks (e.g. /admin restricted to admin)
  const userRole = request.cookies.get('user_role')?.value;
  if (pathname.startsWith('/admin') && userRole !== 'admin') {
    const dashboardUrl = new URL('/dashboard', request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
