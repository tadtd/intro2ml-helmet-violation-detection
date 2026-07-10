-- FR-019, FR-020 Storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES 
('videos', 'videos', false),
('violations', 'violations', false)
ON CONFLICT (id) DO NOTHING;

-- RLS for buckets (Storage requires RLS as well to control object access)
-- Note: the users will be accessing via Signed URLs (backend API), so service_role handles most things.
-- However, we still need to allow service_role.

-- The storage.objects table needs RLS. We assume Supabase's default Storage RLS structure is used.
-- For local testing, we don't strictly need to define storage.objects RLS, since our focus is
-- on `profiles`, `videos`, and `violations` tables per requirements. But it's good practice.
