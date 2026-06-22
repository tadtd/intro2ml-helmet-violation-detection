create table if not exists profiles (
  id uuid references auth.users primary key,
  role text default 'operator' check (role in ('admin', 'operator')),
  full_name text
);

create table if not exists videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  filename text not null,
  model_used text not null,
  status text default 'pending' check (status in ('pending', 'processing', 'done', 'failed')),
  created_at timestamptz default now()
);

create table if not exists violations (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id),
  user_id uuid references auth.users(id),
  track_id int,
  model_used text,
  image_url text,
  timestamp timestamptz default now()
);

alter table profiles enable row level security;
alter table videos enable row level security;
alter table violations enable row level security;

create policy "profiles view own"
  on profiles for select
  using (auth.uid() = id);

create policy "videos view own or admin"
  on videos for select
  using (
    auth.uid() = user_id
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

create policy "violations view own or admin"
  on violations for select
  using (
    auth.uid() = user_id
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
