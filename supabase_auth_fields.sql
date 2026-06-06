-- ============================================================
-- ADD EXPERT USERNAME + PASSWORD TO PROFILES
-- Запустите в Supabase SQL Editor → New query → Run
-- ============================================================

alter table profiles add column if not exists expert_username text unique;
alter table profiles add column if not exists expert_password_hash text;
alter table profiles add column if not exists full_name text;

-- Index for fast username lookup
create index if not exists idx_profiles_expert_username on profiles(expert_username);
