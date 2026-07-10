-- FR-012 Profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
    id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('admin', 'operator')),
    display_name text,
    created_at timestamp with time zone DEFAULT now()
);
