create table if not exists videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  filename text not null,
  storage_path text not null,
  content_type text,
  model_used text not null,
  status text default 'pending' check (status in ('pending', 'processing', 'done', 'failed')),
  created_at timestamptz default now()
);

alter table videos enable row level security;

drop policy if exists "videos view own or admin" on videos;

create policy "videos view own or admin"
  on videos for select
  using (
    auth.uid() = user_id
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
