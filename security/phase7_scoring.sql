-- ============================================================================
-- STRUCTURED EXPERT SCORING. Each review carries per-criterion scores (1..5);
-- the project's overall expert score is the average of reviewers' averages.
-- ============================================================================
alter table reviews add column if not exists scores    jsonb;
alter table reviews add column if not exists score_avg numeric;

-- app_submit_review now also stores the criterion scores + their average.
drop function if exists app_submit_review(text,uuid,text,text);
create or replace function app_submit_review(p_token text, p_review_id uuid, p_decision text, p_text text, p_scores jsonb default null)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare
  uid uuid; me profiles; rev reviews; pr projects;
  total int; voted int; n_app int; n_rej int; n_rev int; maj int;
  new_status text := null; n_type text; n_title text; n_body text; amt int;
  s_sum numeric := 0; s_cnt int := 0; s_avg numeric := null; v numeric;
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

  -- average the provided criterion scores (each clamped to 1..5)
  if p_scores is not null and jsonb_typeof(p_scores) = 'object' then
    for v in select (value)::numeric from jsonb_each_text(p_scores) loop
      if v is not null then
        v := least(5, greatest(1, v));
        s_sum := s_sum + v; s_cnt := s_cnt + 1;
      end if;
    end loop;
    if s_cnt > 0 then s_avg := round(s_sum / s_cnt, 2); end if;
  end if;

  update reviews set decision = p_decision, review_text = p_text, reviewed_at = now(),
                     scores = p_scores, score_avg = s_avg
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
  elsif voted = total and total > 0 then
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
          n_type := 'approved'; n_title := '✅ Ваш проект одобрен экспертами';
          n_body := '"'||pr.title||'" прошёл экспертизу и перешёл на следующий этап!';
        elsif new_status = 'revision' then
          n_type := 'revision'; n_title := '↩️ Проект отправлен на доработку';
          n_body := 'Эксперты вернули "'||pr.title||'" на доработку. Откройте проект — там замечания экспертов, исправьте и отправьте заново.';
        else
          n_type := 'rejected'; n_title := '📢 Проект опубликован в общую ленту';
          n_body := '"'||pr.title||'" отклонён экспертами, но опубликован в ленту для обсуждения.';
        end if;
        insert into notifications(user_id, type, title, body, project_id, is_read, tg_pushed)
          values (pr.user_id, n_type, n_title, n_body, rev.project_id, false, false);
      end if;
    end if;
  end if;

  return jsonb_build_object('new_status', new_status, 'project_id', rev.project_id, 'xp', amt, 'score_avg', s_avg);
end $$;
grant execute on function app_submit_review(text,uuid,text,text,jsonb) to anon, authenticated;

-- Aggregate expert score for a project (avg of reviewers' averages) — admin/public read.
create or replace function project_score(p_project_id uuid)
returns jsonb language sql stable
set search_path = public, extensions
as $$
  select jsonb_build_object(
    'avg', round(avg(score_avg), 2),
    'count', count(*) filter (where score_avg is not null)
  ) from reviews where project_id = p_project_id and score_avg is not null
$$;
grant execute on function project_score(uuid) to anon, authenticated;
