-- ============================================================
-- NOTIFICATIONS + COMMENT REPLIES
-- Запустите в Supabase SQL Editor → New query → Run
-- ============================================================

-- 1. Добавить parent_id в comments (для ответов на комментарии)
alter table comments add column if not exists parent_id uuid references comments(id) on delete cascade;

-- 2. Таблица уведомлений
create table if not exists notifications (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references profiles(id) on delete cascade,
  type        text not null,
  title       text not null,
  body        text,
  project_id  uuid references projects(id) on delete set null,
  is_read     boolean default false,
  created_at  timestamptz default now()
);

alter table notifications enable row level security;
create policy "notif_select" on notifications for select using (true);
create policy "notif_insert" on notifications for insert with check (true);
create policy "notif_update" on notifications for update using (true);

-- 3. Добавить comments в realtime publication (если не добавлен)
-- (comments уже должен быть там из прошлого шага)
