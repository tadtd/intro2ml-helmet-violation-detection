-- supabase/tests/seed_10k.sql
-- Seed script to generate 10,000 records for performance benchmarking (SC-005)

BEGIN;

-- 1. Create a dummy admin and operator for the benchmark if they don't exist
INSERT INTO auth.users (id, email)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'admin_bench@test.local'),
    ('00000000-0000-0000-0000-000000000002', 'operator_bench@test.local')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.profiles (id, display_name, role)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'Admin Benchmark', 'admin'),
    ('00000000-0000-0000-0000-000000000002', 'Operator Benchmark', 'operator')
ON CONFLICT (id) DO NOTHING;

-- 2. Insert 10,000 violations
-- We use generate_series to quickly bulk insert records.
-- Half will belong to admin, half to operator.
-- Model used alternates between YOLO, RT-DETR, Faster R-CNN.
INSERT INTO public.violations (user_id, video_id, timestamp, confidence, model_used, reviewed, verdict)
SELECT 
    CASE WHEN i % 2 = 0 THEN '00000000-0000-0000-0000-000000000001'::uuid ELSE '00000000-0000-0000-0000-000000000002'::uuid END,
    NULL, -- Independent live stream violations for simplicity
    now() - (i || ' minutes')::interval,
    random(),
    CASE 
        WHEN i % 3 = 0 THEN 'YOLO'
        WHEN i % 3 = 1 THEN 'RT-DETR'
        ELSE 'Faster R-CNN'
    END,
    CASE WHEN i % 5 = 0 THEN true ELSE false END,
    CASE WHEN i % 5 = 0 THEN 'confirmed' ELSE NULL END
FROM generate_series(1, 10000) AS i;

COMMIT;

-- 3. Run EXPLAIN ANALYZE to verify index usage and <2s latency (SC-005)
-- Typical query: filtering by user, status (reviewed/verdict), model, and ordering by timestamp
EXPLAIN ANALYZE 
SELECT * 
FROM public.violations 
WHERE user_id = '00000000-0000-0000-0000-000000000002'::uuid 
  AND reviewed = false 
  AND model_used = 'YOLO'
ORDER BY timestamp DESC
LIMIT 50;
