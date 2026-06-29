# Supabase Schema

Run the schema modules in this order from the Supabase SQL editor:

1. `schema/01_profiles.sql`
2. `schema/02_videos.sql`
3. `schema/03_violations.sql`
4. `schema/04_indexes.sql`
5. `schema/05_realtime.sql`

The files are split by table/domain. Each module creates its table, enables row
level security, and installs the policies owned by that table.

See `../../docs/supabase-setup.md` for bucket policy decisions, verification
steps, and rollback notes.

