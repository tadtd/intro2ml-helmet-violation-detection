-- FR-018 Helper: is_admin() function with SECURITY DEFINER to avoid RLS infinite recursion
-- This function reads from public.profiles bypassing RLS (runs as the function owner/postgres)
-- so the admin policies on videos/violations/profiles can call it safely.

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
