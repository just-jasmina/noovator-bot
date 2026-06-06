-- ============================================================
-- RLS FIX — убираем зависимость от Supabase Auth
-- Запустите в Supabase SQL Editor → New query → Run
-- ============================================================

-- Drop old auth-based policies
drop policy if exists "profiles_insert" on profiles;
drop policy if exists "profiles_update" on profiles;
drop policy if exists "projects_insert" on projects;
drop policy if exists "projects_update" on projects;
drop policy if exists "comments_insert" on comments;
drop policy if exists "likes_insert" on likes;
drop policy if exists "likes_delete" on likes;
drop policy if exists "xp_select" on xp_transactions;
drop policy if exists "xp_insert" on xp_transactions;
drop policy if exists "reviews_select" on reviews;
drop policy if exists "reviews_update" on reviews;

-- Profiles: public read + write (Telegram Mini App, auth via tg)
create policy "profiles_insert" on profiles for insert with check (true);
create policy "profiles_update" on profiles for update using (true);

-- Projects: public insert/update
create policy "projects_insert" on projects for insert with check (true);
create policy "projects_update" on projects for update using (true);

-- Comments: public insert
create policy "comments_insert" on comments for insert with check (true);

-- Likes: public insert/delete
create policy "likes_insert" on likes for insert with check (true);
create policy "likes_delete" on likes for delete using (true);

-- XP: public read + insert
create policy "xp_select" on xp_transactions for select using (true);
create policy "xp_insert" on xp_transactions for insert with check (true);

-- Reviews: public read + update
create policy "reviews_select" on reviews for select using (true);
create policy "reviews_update" on reviews for update using (true);
create policy "reviews_insert" on reviews for insert with check (true);
