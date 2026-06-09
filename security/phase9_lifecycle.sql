-- ============================================================================
-- PROJECT LIFECYCLE + CURATOR ROLE. After expert approval, a Ministry curator
-- advances a project: Одобрен → Пилот → Масштаб → Внедрён. Each milestone
-- awards the author XP and notifies them. Curator-only, server-side.
-- ============================================================================

-- 0) allow the 'curator' (and 'moderator') role.
alter table profiles drop constraint if exists profiles_role_check;
alter table profiles add constraint profiles_role_check
  check (role = any (array['user','expert','admin','curator','moderator']));

-- 1) anon can't self-promote to curator (extend the escalation guard).
create or replace function block_priv_escalation()
returns trigger language plpgsql as $$
begin
  if current_user in ('anon','authenticated')
     and NEW.role in ('admin','moderator','expert','curator')
     and (TG_OP='INSERT' or OLD.role is distinct from NEW.role) then
    raise exception 'role escalation to % is not allowed', NEW.role;
  end if;
  return NEW;
end $$;

-- 2) Curator advances a project one (or more) stages forward.
create or replace function app_advance_project(p_token text, p_project_id uuid, p_new_status text)
returns jsonb language plpgsql security definer
set search_path = public, extensions
as $$
declare
  uid uuid; r text; pr projects; cur_o int; new_o int; amt int; lbl text;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select role into r from profiles where id = uid;
  if r <> 'curator' then raise exception 'curators only'; end if;

  select * into pr from projects where id = p_project_id;
  if pr.id is null then raise exception 'project not found'; end if;

  cur_o := case pr.status when 'approved' then 1 when 'pilot' then 2 when 'scale' then 3 when 'scaled' then 4 else 0 end;
  new_o := case p_new_status when 'pilot' then 2 when 'scale' then 3 when 'scaled' then 4 else 0 end;
  if new_o = 0 then raise exception 'bad target stage'; end if;
  if cur_o = 0 then raise exception 'project must be approved first'; end if;
  if new_o <= cur_o then raise exception 'can only move forward'; end if;

  update projects set status = p_new_status where id = p_project_id;

  amt := case p_new_status when 'pilot' then 500 when 'scale' then 1000 when 'scaled' then 1500 else 0 end;
  lbl := case p_new_status when 'pilot' then 'Пилот' when 'scale' then 'Масштаб' when 'scaled' then 'Внедрён' else p_new_status end;

  if pr.user_id is not null then
    if amt > 0 then
      insert into xp_transactions(user_id, amount, reason, icon)
        values (pr.user_id, amt, 'Этап проекта: '||lbl, '🚀');
      update profiles set season_xp = coalesce(season_xp,0)+amt, global_xp = coalesce(global_xp,0)+amt
        where id = pr.user_id and role <> 'admin';
    end if;
    insert into notifications(user_id, type, title, body, project_id, is_read, tg_pushed)
      values (pr.user_id, 'stage', '🚀 Новый этап проекта',
              '"'||pr.title||'" переведён на этап «'||lbl||'»'||case when amt>0 then '. +'||amt||' XP' else '' end,
              p_project_id, false, false);
  end if;

  return jsonb_build_object('status', p_new_status, 'xp', amt);
end $$;
grant execute on function app_advance_project(text,uuid,text) to anon, authenticated;
