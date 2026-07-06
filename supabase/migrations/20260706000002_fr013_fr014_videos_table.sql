-- FR-013, FR-014 Videos table
CREATE TABLE IF NOT EXISTS public.videos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'pending',
    error_message text,
    progress_pct integer NOT NULL DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100),
    processed_at timestamp with time zone,
    model_used text CHECK (model_used IN ('YOLO', 'RT-DETR', 'Faster R-CNN')),
    created_at timestamp with time zone DEFAULT now()
);
