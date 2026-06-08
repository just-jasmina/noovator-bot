-- ============================================================================
-- SECURITY PHASE 1 (additive, deploy BEFORE frontend & BEFORE locks)
-- Lightweight session-token layer + server-side privileged operations.
-- Old frontend keeps working (it just ignores the returned _token and still
-- does direct writes, which remain allowed until Phase 2 locks them down).
-- ============================================================================

-- ---- session store (server-only; anon/PostgREST can never read it) ---------
create table if not exists app_sessions (
  token_hash  text primary key,
  user_id     uuid not null references profiles(id) on delete cascade,
  created_at  timestamptz not null default now(),
  expires_at  timestamptz not null default now() + interval '60 days'
);
alter table app_sessions enable row level security;
revoke all on app_sessions from anon, authenticated, public;

-- ---- helpers (internal only — not callable by anon) ------------------------
create or replace function _app_hash(p text)
returns text language sql immutable
set search_path = public, extensions
as $$ select encode(digest(p, 'sha256'), 'hex') $$;

create or replace function _app_mktoken()
returns text language sql volatile
as $$ select replace(gen_random_uuid()::text,'-','') || replace(gen_random_uuid()::text,'-','') $$;

create or replace function _session_uid(p_token text)
returns uuid language sql stable security definer
set search_path = public, extensions
as $$
  select user_id from app_sessions
  where token_hash = _app_hash(p_token) and expires_at > now()
$$;

revoke execute on function _app_hash(text)     from anon, authenticated, public;
revoke execute on function _app_mktoken()       from anon, authenticated, public;
revoke execute on function _session_uid(text)   from anon, authenticated, public;

-- ---- login: verify password AND mint a session token ----------------------
create or replace function app_login(p_username text, p_hash text)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare r profiles; tok text;
begin
  select * into r from profiles where username = p_username limit 1;
  if r.id is null then return null; end if;
  if r.password_hash is distinct from p_hash then return null; end if;
  tok := _app_mktoken();
  insert into app_sessions(token_hash, user_id) values (_app_hash(tok), r.id);
  return (to_jsonb(r) - 'password_hash' - 'expert_password_hash' - 'pnfl' - 'auth_id')
         || jsonb_build_object('_token', tok);
end $$;

-- ---- resume an existing session (auto-login) ------------------------------
create or replace function app_resume(p_token text)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare uid uuid; r profiles;
begin
  uid := _session_uid(p_token);
  if uid is null then return null; end if;
  update app_sessions set expires_at = now() + interval '60 days'
    where token_hash = _app_hash(p_token);
  select * into r from profiles where id = uid;
  if r.id is null then return null; end if;
  return to_jsonb(r) - 'password_hash' - 'expert_password_hash' - 'pnfl' - 'auth_id';
end $$;

create or replace function app_logout(p_token text)
returns void language sql security definer
set search_path = public, extensions
as $$ delete from app_sessions where token_hash = _app_hash(p_token) $$;

-- ---- XP: server decides the amount from xp_rules (client can't pick) -------
create or replace function app_award_xp(p_token text, p_action text, p_reason text, p_icon text)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare uid uuid; r profiles; amt int;
begin
  uid := _session_uid(p_token);
  if uid is null then return null; end if;
  select * into r from profiles where id = uid;
  if r.id is null then return null; end if;
  if r.role = 'admin' then  -- observer earns nothing
    return jsonb_build_object('season_xp', r.season_xp, 'global_xp', r.global_xp, 'amount', 0);
  end if;
  -- amount is authoritative from xp_rules; only known actions, sane bounds.
  select xp_amount into amt from xp_rules where action = p_action and is_active = true limit 1;
  if amt is null then
    amt := case p_action
      when 'project_submit' then 50 when 'profile_register' then 50
      when 'expert_review'  then 20 when 'comment' then 5
      when 'daily_streak'   then 5  when 'like' then 2 else 0 end;
  end if;
  if amt <= 0 then
    return jsonb_build_object('season_xp', r.season_xp, 'global_xp', r.global_xp, 'amount', 0);
  end if;
  if amt > 2000 then amt := 2000; end if;  -- hard ceiling
  insert into xp_transactions(user_id, amount, reason, icon)
    values (uid, amt, coalesce(p_reason,''), coalesce(p_icon,'⭐'));
  update profiles set season_xp = coalesce(season_xp,0) + amt,
                      global_xp = coalesce(global_xp,0) + amt
    where id = uid;
  return jsonb_build_object('season_xp', coalesce(r.season_xp,0)+amt,
                            'global_xp', coalesce(r.global_xp,0)+amt, 'amount', amt);
end $$;

-- ---- expert review: identity + assignment checked server-side -------------
-- Replaces the client-side review update + vote counting + status change.
create or replace function app_submit_review(p_token text, p_review_id uuid, p_decision text, p_text text)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare
  uid uuid; me profiles; rev reviews; pr projects;
  total int; voted int; n_app int; n_rej int; n_rev int; maj int;
  new_status text := null; n_title text; n_body text; amt int;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select * into me from profiles where id = uid;
  if me.role <> 'expert' then raise exception 'experts only'; end if;
  if p_decision not in ('approve','reject','revision') then raise exception 'bad decision'; end if;

  select * into rev from reviews where id = p_review_id;
  if rev.id is null then raise exception 'review not found'; end if;
  if rev.expert_id <> uid then raise exception 'not your assignment'; end if;
  -- server-side floor on review length (defense-in-depth vs. client's 150 words)
  if coalesce(array_length(regexp_split_to_array(btrim(coalesce(p_text,'')), '\s+'), 1), 0) < 80 then
    raise exception 'review too short';
  end if;

  update reviews set decision = p_decision, review_text = p_text, reviewed_at = now()
    where id = p_review_id;

  -- award the expert their review XP (authoritative)
  select xp_amount into amt from xp_rules where action='expert_review' and is_active limit 1;
  amt := coalesce(amt, 20);
  insert into xp_transactions(user_id, amount, reason, icon)
    values (uid, amt, 'Рецензия проекта / Retsenziya', '🔍');
  update profiles set season_xp = coalesce(season_xp,0)+amt, global_xp = coalesce(global_xp,0)+amt
    where id = uid;

  -- recompute project verdict from ALL of its reviews (majority -> plurality)
  select count(*),
         count(*) filter (where decision is not null),
         count(*) filter (where decision='approve'),
         count(*) filter (where decision='reject'),
         count(*) filter (where decision='revision')
    into total, voted, n_app, n_rej, n_rev
    from reviews where project_id = rev.project_id;
  maj := ceil(total/2.0 + 0.01);

  if    n_app >= maj then new_status := 'approved';
  elsif n_rej >= maj then new_status := 'rejected';
  elsif n_rev >= maj then new_status := null;       -- stays under_review
  elsif voted = total and total > 0 then            -- all voted, no majority -> plurality
    if    n_app >= n_rej and n_app >= n_rev then new_status := 'approved';
    elsif n_rej >= n_app and n_rej >= n_rev then new_status := 'rejected';
    end if;                                          -- revision tie -> stays
  end if;

  if new_status is not null then
    select * into pr from projects where id = rev.project_id;
    if pr.id is not null and pr.status is distinct from new_status then
      update projects set status = new_status where id = rev.project_id;
      if pr.user_id is not null then
        if new_status = 'approved' then
          n_title := '✅ Ваш проект одобрен экспертами';
          n_body  := '"'||pr.title||'" прошёл экспертизу и перешёл на следующий этап!';
        else
          n_title := '📢 Проект опубликован в общую ленту';
          n_body  := '"'||pr.title||'" отклонён экспертами, но опубликован в ленту для обсуждения.';
        end if;
        insert into notifications(user_id, type, title, body, project_id, is_read, tg_pushed)
          values (pr.user_id, new_status, n_title, n_body, rev.project_id, false, false);
      end if;
    end if;
  end if;

  return jsonb_build_object('new_status', new_status, 'project_id', rev.project_id, 'xp', amt);
end $$;

-- ---- expose the public RPCs to the anon role -------------------------------
grant execute on function app_login(text,text)                         to anon, authenticated;
grant execute on function app_resume(text)                             to anon, authenticated;
grant execute on function app_logout(text)                             to anon, authenticated;
grant execute on function app_award_xp(text,text,text,text)            to anon, authenticated;
grant execute on function app_submit_review(text,uuid,text,text)       to anon, authenticated;
