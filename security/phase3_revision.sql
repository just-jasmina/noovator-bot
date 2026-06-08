-- ============================================================================
-- REVISION FLOW (#3). When experts vote "revision", the project goes to a real
-- 'revision' status, the author is notified, sees the feedback, edits and
-- resubmits — which resets the same experts' reviews to pending.
-- ============================================================================

-- 0) allow the 'revision' status (the original CHECK omitted it).
alter table projects drop constraint if exists projects_status_check;
alter table projects add constraint projects_status_check
  check (status = any (array['draft','under_review','revision','approved','rejected',
                             'pilot','scale','scaled','crowdsource','incubation','ministry']));

-- 1) app_submit_review: revision verdict now produces status='revision' and an
--    author notification (was: silently stayed under_review).
create or replace function app_submit_review(p_token text, p_review_id uuid, p_decision text, p_text text)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare
  uid uuid; me profiles; rev reviews; pr projects;
  total int; voted int; n_app int; n_rej int; n_rev int; maj int;
  new_status text := null; n_type text; n_title text; n_body text; amt int;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select * into me from profiles where id = uid;
  if me.role <> 'expert' then raise exception 'experts only'; end if;
  if p_decision not in ('approve','reject','revision') then raise exception 'bad decision'; end if;

  select * into rev from reviews where id = p_review_id;
  if rev.id is null then raise exception 'review not found'; end if;
  if rev.expert_id <> uid then raise exception 'not your assignment'; end if;
  if coalesce(array_length(regexp_split_to_array(btrim(coalesce(p_text,'')), '\s+'), 1), 0) < 80 then
    raise exception 'review too short';
  end if;

  update reviews set decision = p_decision, review_text = p_text, reviewed_at = now()
    where id = p_review_id;

  select xp_amount into amt from xp_rules where action='expert_review' and is_active limit 1;
  amt := coalesce(amt, 20);
  insert into xp_transactions(user_id, amount, reason, icon)
    values (uid, amt, 'Рецензия проекта / Retsenziya', '🔍');
  update profiles set season_xp = coalesce(season_xp,0)+amt, global_xp = coalesce(global_xp,0)+amt
    where id = uid;

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
  elsif n_rev >= maj then new_status := 'revision';
  elsif voted = total and total > 0 then            -- all voted, no majority -> plurality
    if    n_app >= n_rej and n_app >= n_rev then new_status := 'approved';
    elsif n_rej >= n_app and n_rej >= n_rev then new_status := 'rejected';
    else new_status := 'revision';
    end if;
  end if;

  if new_status is not null then
    select * into pr from projects where id = rev.project_id;
    if pr.id is not null and pr.status is distinct from new_status then
      update projects set status = new_status where id = rev.project_id;
      if pr.user_id is not null then
        if new_status = 'approved' then
          n_type := 'approved';
          n_title := '✅ Ваш проект одобрен экспертами';
          n_body  := '"'||pr.title||'" прошёл экспертизу и перешёл на следующий этап!';
        elsif new_status = 'revision' then
          n_type := 'revision';
          n_title := '↩️ Проект отправлен на доработку';
          n_body  := 'Эксперты вернули "'||pr.title||'" на доработку. Откройте проект — там замечания экспертов, исправьте и отправьте заново.';
        else
          n_type := 'rejected';
          n_title := '📢 Проект опубликован в общую ленту';
          n_body  := '"'||pr.title||'" отклонён экспертами, но опубликован в ленту для обсуждения.';
        end if;
        insert into notifications(user_id, type, title, body, project_id, is_read, tg_pushed)
          values (pr.user_id, n_type, n_title, n_body, rev.project_id, false, false);
      end if;
    end if;
  end if;

  return jsonb_build_object('new_status', new_status, 'project_id', rev.project_id, 'xp', amt);
end $$;

-- 2) app_resubmit_project: the author edits the returned project and sends it
--    back to expertise. Ownership + 'revision' status checked server-side; the
--    same reviewers' rows are reset to pending and they are re-notified.
create or replace function app_resubmit_project(p_token text, p_project_id uuid, p_fields jsonb)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare uid uuid; pr projects; e record; n int := 0; sla timestamptz;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select * into pr from projects where id = p_project_id;
  if pr.id is null then raise exception 'project not found'; end if;
  if pr.user_id <> uid then raise exception 'not your project'; end if;
  if pr.status <> 'revision' then raise exception 'project is not in revision'; end if;

  update projects set
      title      = coalesce(nullif(p_fields->>'title',''),      title),
      pitch      = coalesce(nullif(p_fields->>'pitch',''),      pitch),
      problem    = coalesce(nullif(p_fields->>'problem',''),    problem),
      solution   = coalesce(nullif(p_fields->>'solution',''),   solution),
      budget_use = coalesce(p_fields->>'budget_use', budget_use),
      effect     = coalesce(p_fields->>'effect',     effect),
      kpis       = coalesce(
                     (select array_agg(x) from jsonb_array_elements_text(p_fields->'kpis') x
                       where btrim(x) <> ''), kpis),
      status     = 'under_review'
    where id = p_project_id;

  sla := now() + interval '7 days';
  update reviews set decision = null, review_text = null, reviewed_at = null, sla_deadline = sla
    where project_id = p_project_id;

  for e in select expert_id from reviews where project_id = p_project_id loop
    insert into notifications(user_id, type, title, body, project_id, is_read, tg_pushed)
      values (e.expert_id, 'review_assigned', 'Проект доработан автором',
              'Автор учёл замечания и отправил проект на повторную экспертизу.', p_project_id, false, false);
    n := n + 1;
  end loop;

  return jsonb_build_object('ok', true, 'reviewers_notified', n);
end $$;

grant execute on function app_resubmit_project(text,uuid,jsonb) to anon, authenticated;
