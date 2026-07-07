-- Fix script for RLS infinite recursion on live Supabase cloud project
-- Run with: psql "postgresql://..." -f tests/db/fix_rls_recursion.sql

-- Step 1: Create the is_admin() helper (SECURITY DEFINER bypasses RLS when reading profiles)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role = 'admin'
  );
$$;

-- Step 2: Drop old recursive admin policies
DROP POLICY IF EXISTS "Admins can do everything on profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can do everything on videos" ON public.videos;
DROP POLICY IF EXISTS "Admins can do everything on violations" ON public.violations;

-- Step 3: Recreate with is_admin() — no more recursion
CREATE POLICY "Admins can do everything on profiles"
ON public.profiles TO authenticated
USING (public.is_admin());

CREATE POLICY "Admins can do everything on videos"
ON public.videos TO authenticated
USING (public.is_admin());

CREATE POLICY "Admins can do everything on violations"
ON public.violations TO authenticated
USING (public.is_admin());

SELECT 'Done! is_admin() created and policies fixed.' AS status;
