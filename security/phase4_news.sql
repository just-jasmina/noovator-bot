-- ============================================================================
-- NEWS / ONBOARDING (greets users on the feed; fills the empty database).
-- Public read-only; writes only server-side (no anon grant).
-- ============================================================================
create table if not exists news (
  id         uuid primary key default gen_random_uuid(),
  title      text not null,
  title_uz   text,
  body       text not null,
  body_uz    text,
  category   text,                       -- 'Опыт мира' | 'Здравоохранение' | 'Платформа'
  icon       text default '📰',
  link_url   text,
  is_pinned  boolean default false,
  is_active  boolean default true,
  created_at timestamptz default now()
);
alter table news enable row level security;
drop policy if exists news_read on news;
create policy news_read on news for select using (is_active);
grant select on news to anon, authenticated;          -- read-only for the client
revoke insert, update, delete on news from anon, authenticated;

-- Seed welcoming content (idempotent: only if the table is empty).
insert into news (title, title_uz, body, body_uz, category, icon, is_pinned, created_at)
select * from (values
 ('👋 Добро пожаловать в «Tibbiyot Novatorlari»!',
  '👋 «Tibbiyot Novatorlari» platformasiga xush kelibsiz!',
  'Это платформа Минздрава для медицинских инноваций. Подайте свою идею — она пройдёт закрытую экспертизу, попадёт в общую ленту, а вы будете расти в лигах и зарабатывать XP. Лучшие проекты доходят до пилота и внедрения в системе здравоохранения.',
  'Bu — Sogʻliqni saqlash vazirligining tibbiy innovatsiyalar platformasi. Gʻoyangizni yuboring — u yopiq ekspertizadan oʻtadi, umumiy lentaga tushadi, siz esa ligalarda oʻsib, XP toʻplaysiz. Eng yaxshi loyihalar pilot va joriy etishgacha yetadi.',
  'Платформа', '👋', true, now()),

 ('🌍 Эстония: 99% медицины — цифровая',
  '🌍 Estoniya: tibbiyotning 99% raqamli',
  'Мировой опыт: в Эстонии почти все медицинские данные электронные, рецепты — цифровые, а доступ к карте пациента есть у врача в любой точке страны. Это снизило ошибки и время на бумажную работу. Подобные идеи цифровизации — отличная тема для вашего проекта.',
  'Jahon tajribasi: Estoniyada deyarli barcha tibbiy maʼlumotlar elektron, retseptlar raqamli, bemor kartasiga shifokor mamlakatning istalgan nuqtasidan kira oladi. Bu xatolar va qogʻozbozlikni kamaytirdi. Raqamlashtirish gʻoyalari — loyihangiz uchun ajoyib mavzu.',
  'Опыт мира', '🌍', false, now() - interval '1 hour'),

 ('🤖 ИИ помогает ставить диагнозы',
  '🤖 Sunʼiy intellekt tashxis qoʻyishda yordam beradi',
  'В мире ИИ уже используется для скрининга диабетической ретинопатии, анализа КТ и раннего выявления рака. Это не заменяет врача, а ускоряет его работу. Если у вас есть идея применения ИИ в клинике — смело подавайте её на платформу.',
  'Dunyoda SI diabetik retinopatiya skriningi, KT tahlili va saratonni erta aniqlashda qoʻllanmoqda. Bu shifokorni almashtirmaydi, balki ishini tezlashtiradi. Klinikada SI qoʻllash gʻoyangiz boʻlsa — platformaga yuboring.',
  'Опыт мира', '🤖', false, now() - interval '2 hour'),

 ('🇺🇿 Цифровое здравоохранение Узбекистана',
  '🇺🇿 Oʻzbekiston raqamli sogʻliqni saqlash',
  'Узбекистан развивает электронные медкарты, телемедицину и единую систему здравоохранения. Ваши проекты могут стать частью этой трансформации — особенно решения для регионов и сельской медицины.',
  'Oʻzbekiston elektron tibbiy kartalar, telemeditsina va yagona sogʻliqni saqlash tizimini rivojlantirmoqda. Loyihalaringiz ushbu oʻzgarishlarning bir qismi boʻlishi mumkin — ayniqsa hududlar va qishloq tibbiyoti uchun yechimlar.',
  'Здравоохранение', '🇺🇿', false, now() - interval '3 hour'),

 ('🏆 Как работают лиги и сезоны',
  '🏆 Ligalar va mavsumlar qanday ishlaydi',
  'За активность вы получаете XP и поднимаетесь по лигам: Новичок → Любитель → Профессионал → Новатор. Каждый квартал — новый сезон: лучшие повышаются, а Новаторы могут становиться менторами проектов. Чем активнее — тем выше.',
  'Faollik uchun XP olasiz va ligalarda koʻtarilasiz: Boshlovchi → Havaskor → Professional → Novator. Har chorakda — yangi mavsum: eng yaxshilar koʻtariladi, Novatorlar esa loyihalarga mentor boʻlishi mumkin.',
  'Платформа', '🏆', false, now() - interval '4 hour'),

 ('💡 Как подать сильную идею',
  '💡 Kuchli gʻoyani qanday taqdim etish',
  'Сильный проект отвечает на три вопроса: какую проблему решает, как именно, и какой измеримый результат (KPI) даст. Укажите аудиторию, ресурсы и сроки. Чем конкретнее KPI — тем выше шанс пройти экспертизу.',
  'Kuchli loyiha uch savolga javob beradi: qanday muammoni hal qiladi, qanday qilib va qanday oʻlchanadigan natija (KPI) beradi. Auditoriya, resurslar va muddatlarni koʻrsating. KPI qanchalik aniq boʻlsa — ekspertizadan oʻtish imkoni shunchalik yuqori.',
  'Платформа', '💡', false, now() - interval '5 hour')
) as v(title,title_uz,body,body_uz,category,icon,is_pinned,created_at)
where not exists (select 1 from news);
