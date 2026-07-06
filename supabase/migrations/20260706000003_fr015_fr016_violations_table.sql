-- FR-015, FR-016 Violations table
CREATE TABLE IF NOT EXISTS public.violations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    video_id uuid REFERENCES public.videos(id) ON DELETE SET NULL,
    confidence numeric NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reviewed boolean NOT NULL DEFAULT false,
    reviewer_id uuid REFERENCES public.profiles(id) ON DELETE SET NULL,
    verdict text CHECK (verdict IN ('confirmed', 'false positive', 'unclear')),
    model_used text,
    timestamp timestamp with time zone NOT NULL DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);
