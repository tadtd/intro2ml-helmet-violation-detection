-- Enable realtime subscriptions for violation inserts.
-- Run after 04_indexes.sql.

alter table public.violations replica identity full;

do $$
begin
  if exists (
    select 1
    from pg_publication
    where pubname = 'supabase_realtime'
  ) and not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'violations'
  ) then
    execute 'alter publication supabase_realtime add table public.violations';
  end if;
end
$$;
