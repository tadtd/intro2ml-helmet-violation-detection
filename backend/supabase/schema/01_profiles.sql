create table if not exists profiles (
  id uuid references auth.users primary key,
  role text default 'operator' check (role in ('admin', 'operator')),
  full_name text
);

alter table profiles enable row level security;

drop policy if exists "profiles view own" on profiles;

create policy "profiles view own"
  on profiles for select
  using (auth.uid() = id);

