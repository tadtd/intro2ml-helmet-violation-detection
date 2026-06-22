create table if not exists violations (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id),
  user_id uuid references auth.users(id),
  track_id int,
  model_used text,
  image_url text,
  timestamp timestamptz default now()
);

alter table violations enable row level security;

drop policy if exists "violations view own or admin" on violations;

create policy "violations view own or admin"
  on violations for select
  using (
    auth.uid() = user_id
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

