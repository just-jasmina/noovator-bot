-- ============================================================
-- ADD USERNAME + PASSWORD TO PROFILES
-- Запустите в Supabase SQL Editor → New query → Run
-- ============================================================

alter table profiles add column if not exists username text unique;
alter table profiles add column if not exists password_hash text;

-- Index for fast username lookup
create index if not exists idx_profiles_username on profiles(username);
