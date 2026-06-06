-- ============================================================
-- TIBBIYOT NOVATORLARI — Supabase Schema
-- Запустите этот файл в Supabase SQL Editor
-- https://supabase.com → ваш проект → SQL Editor → New query
-- ============================================================

-- ===== PROFILES =====
create table if not exists profiles (
  id            uuid primary key default gen_random_uuid(),
  auth_id       uuid references auth.users(id) on delete cascade,
  telegram_id   bigint unique,
  full_name     text not null,
  phone         text,
  pnfl          text,
  occupation    integer default 0,  -- 0=student, 1=worker, 2=both, 3=unemployed
  workplace     text,
  role          text default 'user' check (role in ('user','expert','admin')),
  status        text default 'active' check (status in ('active','pending','banned')),
  league        text default 'novice' check (league in ('novice','amateur','professional','innovator')),
  season_xp     integer default 0,
  global_xp     integer default 0,
  streak_days   integer default 0,
  expert_tags   text[] default '{}',
  created_at    timestamptz default now()
);

-- ===== PROJECTS =====
create table if not exists projects (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid references profiles(id) on delete cascade,
  title          text not null,
  pitch          text not null,
  tags           text[] default '{}',
  problem        text not null default '',
  solution       text not null default '',
  audience       text[] default '{}',
  kpis           text[] default '{}',
  effect         text default '',
  cost_range     text default '',
  budget_use     text default '',
  timeline       text default '',
  status         text default 'under_review' check (status in ('draft','under_review','approved','rejected','pilot','scale')),
  likes_count    integer default 0,
  comments_count integer default 0,
  created_at     timestamptz default now()
);

-- ===== COMMENTS =====
create table if not exists comments (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  user_id     uuid references profiles(id) on delete cascade,
  text        text not null,
  created_at  timestamptz default now()
);

-- ===== LIKES =====
create table if not exists likes (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  user_id     uuid references profiles(id) on delete cascade,
  created_at  timestamptz default now(),
  unique(project_id, user_id)
);

-- ===== XP TRANSACTIONS =====
create table if not exists xp_transactions (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references profiles(id) on delete cascade,
  amount      integer not null,
  reason      text not null,
  icon        text default '⭐',
  created_at  timestamptz default now()
);

-- ===== REVIEWS =====
create table if not exists reviews (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid references projects(id) on delete cascade,
  expert_id    uuid references profiles(id) on delete cascade,
  decision     text check (decision in ('approve','reject','revision')),
  review_text  text,
  reviewed_at  timestamptz,
  sla_deadline timestamptz default (now() + interval '7 days'),
  created_at   timestamptz default now()
);

-- ===== RPC: increment/decrement likes =====
create or replace function increment_likes(proj_id uuid)
returns void language plpgsql as $$
begin
  update projects set likes_count = likes_count + 1 where id = proj_id;
end;
$$;

create or replace function decrement_likes(proj_id uuid)
returns void language plpgsql as $$
begin
  update projects set likes_count = greatest(0, likes_count - 1) where id = proj_id;
end;
$$;

create or replace function increment_comments(proj_id uuid)
returns void language plpgsql as $$
begin
  update projects set comments_count = comments_count + 1 where id = proj_id;
end;
$$;

-- ===== RLS POLICIES =====
alter table profiles enable row level security;
alter table projects enable row level security;
alter table comments enable row level security;
alter table likes enable row level security;
alter table xp_transactions enable row level security;
alter table reviews enable row level security;

-- Profiles: all can read, only owner updates
create policy "profiles_select" on profiles for select using (true);
create policy "profiles_insert" on profiles for insert with check (auth.uid() = auth_id);
create policy "profiles_update" on profiles for update using (auth.uid() = auth_id);

-- Projects: all can read, authenticated insert their own
create policy "projects_select" on projects for select using (true);
create policy "projects_insert" on projects for insert with check (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
);
create policy "projects_update" on projects for update using (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
  or exists (select 1 from profiles where profiles.auth_id = auth.uid() and profiles.role = 'admin')
);

-- Comments: all read, authenticated insert
create policy "comments_select" on comments for select using (true);
create policy "comments_insert" on comments for insert with check (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
);

-- Likes: all read, authenticated insert/delete own
create policy "likes_select" on likes for select using (true);
create policy "likes_insert" on likes for insert with check (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
);
create policy "likes_delete" on likes for delete using (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
);

-- XP: only owner reads own
create policy "xp_select" on xp_transactions for select using (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
);
create policy "xp_insert" on xp_transactions for insert with check (
  exists (select 1 from profiles where profiles.id = user_id and profiles.auth_id = auth.uid())
);

-- Reviews: experts see their own
create policy "reviews_select" on reviews for select using (
  exists (select 1 from profiles where profiles.id = expert_id and profiles.auth_id = auth.uid())
  or exists (select 1 from profiles where profiles.auth_id = auth.uid() and profiles.role = 'admin')
);
create policy "reviews_update" on reviews for update using (
  exists (select 1 from profiles where profiles.id = expert_id and profiles.auth_id = auth.uid())
);

-- ===== SEED DATA (демо пользователи и проекты) =====
-- Демо профили (без реального auth_id — только для отображения)
insert into profiles (id, full_name, phone, occupation, workplace, role, league, season_xp, global_xp, status)
values
  ('11111111-0000-0000-0000-000000000001', 'Малика Хасанова', '+998901234567', 1, 'Министерство здравоохранения', 'admin', 'innovator', 4200, 8900, 'active'),
  ('11111111-0000-0000-0000-000000000002', 'Азиз Каримов', '+998907654321', 1, 'РСНПМЦ кардиологии', 'expert', 'professional', 2100, 3400, 'active'),
  ('11111111-0000-0000-0000-000000000003', 'Нилуфар Юсупова', '+998995551234', 0, 'Ташкентский медицинский институт', 'expert', 'professional', 1800, 2200, 'active'),
  ('11111111-0000-0000-0000-000000000004', 'Санжар Умаров', '+998993334455', 1, 'Республиканский онкоцентр', 'user', 'amateur', 620, 850, 'active'),
  ('11111111-0000-0000-0000-000000000005', 'Диёра Расулова', '+998977778899', 0, 'Самаркандский государственный медицинский университет', 'user', 'novice', 150, 150, 'active')
on conflict (id) do nothing;

-- Демо проекты
insert into projects (user_id, title, pitch, tags, problem, solution, audience, kpis, effect, cost_range, budget_use, timeline, status, likes_count, comments_count)
values
  ('11111111-0000-0000-0000-000000000002',
   'AI-диагностика туберкулёза по рентгеновским снимкам',
   'Система машинного обучения для ранней диагностики туберкулёза по рентгеновским снимкам с точностью 94%. Позволяет снизить нагрузку на врачей-рентгенологов в 3 раза.',
   ARRAY['ИИ в медицине','Лаборатория','Мед. образование'],
   'Ежегодно в Узбекистане выявляется более 20 000 новых случаев туберкулёза. Дефицит квалифицированных рентгенологов приводит к задержкам диагностики на 2–4 недели.',
   'Нейросеть на базе ResNet-50, обученная на 50 000 рентгеновских снимков, с интеграцией в существующие PACS-системы больниц.',
   ARRAY['Врачи','IT-служба'],
   ARRAY['Точность диагностики >93%','Время анализа снимка <30 сек','Снижение пропущенных случаев на 40%'],
   'Сокращение времени постановки диагноза с 14 дней до 1 дня для 80% пациентов.',
   'До 100 млн сум', 'Серверное оборудование, разработка API, обучение персонала', '1–3 месяца',
   'approved', 42, 8),

  ('11111111-0000-0000-0000-000000000001',
   'Умная очередь в государственных поликлиниках',
   'Мобильное приложение для электронной записи и управления очередью в 450 государственных поликлиниках Узбекистана. Интеграция с ЕГИСЗ.',
   ARRAY['IT и Цифровизация','Орг. здравоохранения'],
   'Среднее время ожидания в очереди в государственных поликлиниках составляет 2–3 часа. Ежегодно регистрируется более 5 млн часов потерянного рабочего времени пациентов.',
   'Мобильное приложение с электронными талонами, SMS-уведомлениями и прогнозированием времени ожидания на основе ML.',
   ARRAY['Пациенты','Управленцы','IT-служба'],
   ARRAY['Среднее время ожидания <30 мин','Охват 200+ поликлиник за 6 мес','NPS пациентов >60'],
   'Экономия 2+ млн рабочих часов пациентов ежегодно. Снижение жалоб на 70%.',
   'Более 100 млн сум', 'Разработка приложения, интеграция с МИС, маркетинг', 'До 6 месяцев',
   'pilot', 87, 23),

  ('11111111-0000-0000-0000-000000000003',
   'Телемедицина для сельских районов с низким интернетом',
   'Платформа видеоконсультаций для пациентов в отдалённых районах, оптимизированная для работы при скорости интернета от 100 кбит/с.',
   ARRAY['IT и Цифровизация','Орг. здравоохранения'],
   '35% населения Узбекистана проживает в сельских районах с ограниченным доступом к квалифицированной медицинской помощи.',
   'Лёгкое приложение с адаптивным видеокодеком H.265, асинхронными консультациями и офлайн-режимом для хранения медкарт.',
   ARRAY['Пациенты','Врачи'],
   ARRAY['Проведено 10 000+ консультаций за год','Охват 50 сельских районов','Время ответа врача <24 часа'],
   'Доступ к медицинской помощи для 500 000+ человек в отдалённых районах.',
   'До 100 млн сум', 'Разработка, серверы, партнёрство с операторами', '1–3 месяца',
   'under_review', 31, 5),

  ('11111111-0000-0000-0000-000000000004',
   'Автоматизация учёта лекарств в аптеках',
   'IoT-система для автоматического контроля остатков лекарств, температурного режима и учёта сроков годности в аптечных складах.',
   ARRAY['IT и Цифровизация','Фармакология'],
   'Ежегодные потери фармацевтической отрасли от просроченных лекарств — более $10 млн. Ручной учёт занимает 4–6 часов в день.',
   'RFID-метки + IoT-датчики + облачная платформа для мониторинга в реальном времени с интеграцией в 1С.',
   ARRAY['Аптеки','Управленцы'],
   ARRAY['Снижение потерь от просрочки на 80%','Экономия 3+ часов в день на учёте','ROI 200% за 12 месяцев'],
   'Предотвращение потерь на 8 млн сум ежемесячно для средней аптечной сети.',
   'До 100 млн сум', 'Оборудование IoT, разработка ПО, интеграция', 'До 6 месяцев',
   'approved', 19, 3),

  ('11111111-0000-0000-0000-000000000005',
   'Геймификация вакцинации детей',
   'Мобильное приложение-игра для повышения охвата вакцинацией среди детей 0–5 лет через геймификацию и образование родителей.',
   ARRAY['Педиатрия','Мед. образование'],
   'Охват вакцинацией детей в Узбекистане снизился с 99% до 91% за последние 5 лет из-за роста антипрививочных настроений.',
   'Приложение с игровыми механиками для детей и образовательным контентом для родителей. Система напоминаний и QR-кодов для поликлиник.',
   ARRAY['Пациенты','Врачи'],
   ARRAY['Охват вакцинацией +5% за год','100 000+ активных пользователей','Снижение пропущенных доз на 30%'],
   'Предотвращение 50 000+ случаев предотвратимых заболеваний ежегодно.',
   'До 10 млн сум', 'Разработка приложения, дизайн, маркетинг', '1–3 месяца',
   'under_review', 12, 2)
on conflict do nothing;

-- Seed XP transactions for demo users
insert into xp_transactions (user_id, amount, reason, icon)
values
  ('11111111-0000-0000-0000-000000000001', 50, 'Бонус за регистрацию', '✅'),
  ('11111111-0000-0000-0000-000000000001', 50, 'Подача проекта', '📤'),
  ('11111111-0000-0000-0000-000000000001', 500, 'Проект вышел в Пилот', '🚀'),
  ('11111111-0000-0000-0000-000000000002', 50, 'Бонус за регистрацию', '✅'),
  ('11111111-0000-0000-0000-000000000002', 50, 'Подача проекта', '📤'),
  ('11111111-0000-0000-0000-000000000002', 20, 'Рецензия проекта', '🔍'),
  ('11111111-0000-0000-0000-000000000004', 50, 'Бонус за регистрацию', '✅'),
  ('11111111-0000-0000-0000-000000000004', 50, 'Подача проекта', '📤'),
  ('11111111-0000-0000-0000-000000000005', 50, 'Бонус за регистрацию', '✅'),
  ('11111111-0000-0000-0000-000000000005', 50, 'Подача проекта', '📤')
on conflict do nothing;
