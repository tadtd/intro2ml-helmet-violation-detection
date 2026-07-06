-- FR-017 Indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON public.videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON public.videos(status);

CREATE INDEX IF NOT EXISTS idx_violations_user_id ON public.violations(user_id);
CREATE INDEX IF NOT EXISTS idx_violations_video_id ON public.violations(video_id);
CREATE INDEX IF NOT EXISTS idx_violations_reviewed ON public.violations(reviewed);
