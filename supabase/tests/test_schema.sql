BEGIN;

-- Run pgTAP tests
SELECT plan(20);

-- Verify auth/storage shim works (so we know our setup is valid)
SELECT has_table('auth', 'users', 'auth.users table should exist');
SELECT has_table('storage', 'buckets', 'storage.buckets table should exist');

-- Profiles tests
SELECT has_table('public', 'profiles', 'profiles table should exist');
SELECT has_column('public', 'profiles', 'role', 'profiles should have role column');

-- Check constraints for profiles
-- Should succeed
INSERT INTO auth.users (id) VALUES ('00000000-0000-0000-0000-000000000001');
SELECT lives_ok(
    $$ INSERT INTO public.profiles (id, role) VALUES ('00000000-0000-0000-0000-000000000001', 'operator') $$,
    'should allow operator role'
);

-- Should fail due to constraint
SELECT throws_ok(
    $$ INSERT INTO public.profiles (id, role) VALUES ('00000000-0000-0000-0000-000000000002', 'hacker') $$,
    'new row for relation "profiles" violates check constraint "profiles_role_check"',
    'should reject invalid roles'
);

-- Videos schema tests
SELECT has_table('public', 'videos', 'videos table should exist');
SELECT has_column('public', 'videos', 'progress_pct', 'videos should have progress_pct column');
SELECT col_default_is('public', 'videos', 'progress_pct', 0, 'progress_pct defaults to 0');
SELECT col_default_is('public', 'videos', 'status', 'pending', 'status defaults to pending');

-- Check constraints for videos
SELECT throws_ok(
    $$ INSERT INTO public.videos (user_id, progress_pct) VALUES ('00000000-0000-0000-0000-000000000001', 150) $$,
    'new row for relation "videos" violates check constraint "videos_progress_pct_check"',
    'should reject progress_pct > 100'
);

SELECT throws_ok(
    $$ INSERT INTO public.videos (user_id, model_used) VALUES ('00000000-0000-0000-0000-000000000001', 'BadModel') $$,
    'new row for relation "videos" violates check constraint "videos_model_used_check"',
    'should reject invalid model_used'
);

SELECT lives_ok(
    $$ INSERT INTO public.videos (id, user_id, model_used, progress_pct) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'YOLO', 50) $$,
    'should allow valid video insert'
);

-- Violations schema tests
SELECT has_table('public', 'violations', 'violations table should exist');
SELECT has_column('public', 'violations', 'confidence', 'violations should have confidence column');
SELECT col_default_is('public', 'violations', 'reviewed', false, 'reviewed defaults to false');

-- Check constraints for violations
SELECT throws_ok(
    $$ INSERT INTO public.violations (user_id, video_id, confidence) VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', 1.5) $$,
    'new row for relation "violations" violates check constraint "violations_confidence_check"',
    'should reject confidence > 1'
);

SELECT throws_ok(
    $$ INSERT INTO public.violations (user_id, video_id, confidence) VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', -0.5) $$,
    'new row for relation "violations" violates check constraint "violations_confidence_check"',
    'should reject confidence < 0'
);

SELECT throws_ok(
    $$ INSERT INTO public.violations (user_id, video_id, confidence, verdict) VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', 0.9, 'maybe') $$,
    'new row for relation "violations" violates check constraint "violations_verdict_check"',
    'should reject invalid verdict'
);

SELECT lives_ok(
    $$ INSERT INTO public.violations (user_id, video_id, confidence, verdict) VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', 0.9, 'confirmed') $$,
    'should allow valid violation insert'
);

SELECT * FROM finish();

ROLLBACK;
