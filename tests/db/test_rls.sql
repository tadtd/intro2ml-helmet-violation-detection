BEGIN;

-- Run pgTAP tests
SELECT plan(6);

-- Setup test users
INSERT INTO auth.users (id) VALUES 
('00000000-0000-0000-0000-000000000001'), -- admin
('00000000-0000-0000-0000-000000000002'), -- op1
('00000000-0000-0000-0000-000000000003'); -- op2

INSERT INTO public.profiles (id, role, display_name) VALUES 
('00000000-0000-0000-0000-000000000001', 'admin', 'Admin User'),
('00000000-0000-0000-0000-000000000002', 'operator', 'Op 1'),
('00000000-0000-0000-0000-000000000003', 'operator', 'Op 2');

INSERT INTO public.videos (id, user_id, status) VALUES 
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'pending'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', 'pending');

-- Test RLS for Operator 1
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000002';

SELECT results_eq(
    'SELECT id FROM public.videos',
    $$VALUES ('10000000-0000-0000-0000-000000000001'::uuid)$$,
    'Operator 1 should only see their own videos'
);

SELECT results_eq(
    'SELECT display_name FROM public.profiles',
    $$VALUES ('Op 1'::text)$$,
    'Operator 1 should only see their own profile'
);

-- Test RLS for Operator 2
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000003';

SELECT results_eq(
    'SELECT id FROM public.videos',
    $$VALUES ('10000000-0000-0000-0000-000000000002'::uuid)$$,
    'Operator 2 should only see their own videos'
);

SELECT results_eq(
    'SELECT display_name FROM public.profiles',
    $$VALUES ('Op 2'::text)$$,
    'Operator 2 should only see their own profile'
);

-- Test RLS for Admin
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';

SELECT is(
    (SELECT count(*) FROM public.videos),
    2::bigint,
    'Admin should see all videos'
);

SELECT is(
    (SELECT count(*) FROM public.profiles),
    3::bigint,
    'Admin should see all profiles'
);

-- Reset role
RESET ROLE;

SELECT * FROM finish();

ROLLBACK;
