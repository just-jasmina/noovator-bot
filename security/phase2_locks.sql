-- ============================================================================
-- SECURITY PHASE 2 (locks) — apply AFTER the token-based frontend is live.
-- Closes the write-side holes the anon key left open. SECURITY DEFINER RPCs run
-- as the table owner (current_user='postgres'), so they bypass every guard here;
-- only the public anon/authenticated path is restricted.
-- ============================================================================

-- 1) Privilege escalation: anon can no longer become expert/admin/moderator.
--    (Seeding new experts is done server-side as postgres, which bypasses.)
create or replace function block_priv_escalation()
returns trigger language plpgsql as $$
begin
  if current_user in ('anon','authenticated')
     and NEW.role in ('admin','moderator','expert')
     and (TG_OP='INSERT' or OLD.role is distinct from NEW.role) then
    raise exception 'role escalation to % is not allowed', NEW.role;
  end if;
  return NEW;
end $$;

-- 2) Profiles: pin XP / league / role / status against the anon path.
--    Other columns (name, region, telegram_id, streak) still update freely.
create or replace function guard_profile_writes()
returns trigger language plpgsql as $$
begin
  if current_user in ('anon','authenticated') then
    if TG_OP='INSERT' then
      NEW.season_xp := 0;
      NEW.global_xp := 0;
      if NEW.league is null then NEW.league := 'novice'; end if;
    elsif TG_OP='UPDATE' then
      NEW.season_xp := OLD.season_xp;   -- XP only via app_award_xp / app_submit_review
      NEW.global_xp := OLD.global_xp;
      NEW.league    := OLD.league;      -- league only via season CRON
      NEW.role      := OLD.role;
      NEW.status    := OLD.status;      -- expert active/inactive not client-editable
    end if;
  end if;
  return NEW;
end $$;
drop trigger if exists trg_guard_profile_writes on profiles;
create trigger trg_guard_profile_writes
  before insert or update on profiles
  for each row execute function guard_profile_writes();

-- 3) Projects: anon can never set a verdict status. Inserts are forced to
--    under_review; status changes from the anon path are rejected.
create or replace function guard_project_status()
returns trigger language plpgsql as $$
begin
  if current_user in ('anon','authenticated') then
    if TG_OP='INSERT' then
      if NEW.status is null or NEW.status not in ('draft','under_review') then
        NEW.status := 'under_review';
      end if;
    elsif TG_OP='UPDATE' and NEW.status is distinct from OLD.status then
      raise exception 'project status is set by experts only (server-side)';
    end if;
  end if;
  return NEW;
end $$;
drop trigger if exists trg_guard_project_status on projects;
create trigger trg_guard_project_status
  before insert or update on projects
  for each row execute function guard_project_status();

-- 4) Reviews: anon may only create *blank* assignment rows. A verdict (decision/
--    text) can never be written or altered from the client — only by the RPC.
create or replace function guard_review_writes()
returns trigger language plpgsql as $$
begin
  if current_user in ('anon','authenticated') then
    if TG_OP='INSERT' then
      NEW.decision    := null;
      NEW.review_text := null;
      NEW.reviewed_at := null;
    elsif TG_OP='UPDATE' then
      NEW.decision    := OLD.decision;
      NEW.review_text := OLD.review_text;
      NEW.reviewed_at := OLD.reviewed_at;
    end if;
  end if;
  return NEW;
end $$;
drop trigger if exists trg_guard_review_writes on reviews;
create trigger trg_guard_review_writes
  before insert or update on reviews
  for each row execute function guard_review_writes();

-- 5) No mass deletion. The app only ever deletes from `likes`, so revoking
--    DELETE/TRUNCATE on the core tables costs nothing and stops wipe attacks.
revoke delete, truncate on profiles from anon, authenticated;
revoke delete, truncate on projects from anon, authenticated;
revoke delete, truncate on reviews  from anon, authenticated;
