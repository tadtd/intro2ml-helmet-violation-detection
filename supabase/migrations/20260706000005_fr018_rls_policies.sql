-- FR-018 RLS policies for profiles and videos
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;

-- Give usage access to authenticated and service_role
GRANT USAGE ON SCHEMA public TO authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated, service_role;

-- Profiles policies
-- Operators can read their own profile
CREATE POLICY "Operators can view own profile" 
ON public.profiles FOR SELECT TO authenticated
USING (auth.uid() = id);

-- Operators can update their own display_name
CREATE POLICY "Operators can update own profile" 
ON public.profiles FOR UPDATE TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Admins can do everything (uses is_admin() SECURITY DEFINER to avoid recursive policy loop)
CREATE POLICY "Admins can do everything on profiles" 
ON public.profiles TO authenticated
USING (public.is_admin());

-- Service role bypasses RLS implicitly if it has BYPASSRLS attribute, or we can explicitly allow
CREATE POLICY "Service role can do everything on profiles" 
ON public.profiles TO service_role
USING (true)
WITH CHECK (true);

-- Videos policies
-- Operators can view and update their own videos
CREATE POLICY "Operators can view own videos" 
ON public.videos FOR SELECT TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Operators can insert own videos" 
ON public.videos FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Operators can update own videos" 
ON public.videos FOR UPDATE TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Admins can do everything (uses is_admin() to avoid recursive policy)
CREATE POLICY "Admins can do everything on videos" 
ON public.videos TO authenticated
USING (public.is_admin());

-- Service role bypasses
CREATE POLICY "Service role can do everything on videos" 
ON public.videos TO service_role
USING (true)
WITH CHECK (true);

-- Violations policies
ALTER TABLE public.violations ENABLE ROW LEVEL SECURITY;

-- Operators can view and update their own violations
CREATE POLICY "Operators can view own violations" 
ON public.violations FOR SELECT TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Operators can insert own violations" 
ON public.violations FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Operators can update own violations" 
ON public.violations FOR UPDATE TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Admins can do everything (uses is_admin() to avoid recursive policy)
CREATE POLICY "Admins can do everything on violations" 
ON public.violations TO authenticated
USING (public.is_admin());

-- Service role bypasses
CREATE POLICY "Service role can do everything on violations" 
ON public.violations TO service_role
USING (true)
WITH CHECK (true);
