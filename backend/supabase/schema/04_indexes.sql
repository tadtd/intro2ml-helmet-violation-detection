-- Additive indexes for dashboard and lookup paths.
-- Run after 03_violations.sql.

create index if not exists idx_videos_user_id
  on public.videos (user_id);

create index if not exists idx_videos_created_at
  on public.videos (created_at);

create index if not exists idx_violations_user_id
  on public.violations (user_id);

create index if not exists idx_violations_video_id
  on public.violations (video_id);

create index if not exists idx_violations_timestamp
  on public.violations ("timestamp");
