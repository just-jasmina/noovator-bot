-- ============================================================================
-- ADMIN NEWS MANAGEMENT. Writes to `news` stay revoked from anon; the admin
-- manages news through these SECURITY DEFINER RPCs, which verify the caller's
-- session token maps to a role='admin' profile.
-- ============================================================================

-- list ALL news (incl. inactive) — admin only
create or replace function app_news_all(p_token text)
returns setof news language plpgsql security definer
set search_path = public, extensions
as $$
declare uid uuid; r text;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select role into r from profiles where id = uid;
  if r <> 'admin' then raise exception 'admin only'; end if;
  return query select * from news order by is_pinned desc, created_at desc;
end $$;

-- create (no id) or update (with id) — admin only
create or replace function app_news_upsert(p_token text, p_news jsonb)
returns uuid language plpgsql security definer
set search_path = public, extensions
as $$
declare uid uuid; r text; nid uuid;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select role into r from profiles where id = uid;
  if r <> 'admin' then raise exception 'admin only'; end if;

  nid := nullif(p_news->>'id','')::uuid;
  if nid is null then
    if coalesce(nullif(p_news->>'title',''),'') = '' or coalesce(nullif(p_news->>'body',''),'') = '' then
      raise exception 'title and body required';
    end if;
    insert into news(title, title_uz, body, body_uz, category, icon, link_url, is_pinned, is_active)
    values (p_news->>'title', nullif(p_news->>'title_uz',''), p_news->>'body', nullif(p_news->>'body_uz',''),
            nullif(p_news->>'category',''), coalesce(nullif(p_news->>'icon',''),'📰'),
            nullif(p_news->>'link_url',''),
            coalesce((p_news->>'is_pinned')::boolean, false),
            coalesce((p_news->>'is_active')::boolean, true))
    returning id into nid;
  else
    update news set
      title     = coalesce(nullif(p_news->>'title',''), title),
      title_uz  = coalesce(p_news->>'title_uz', title_uz),
      body      = coalesce(nullif(p_news->>'body',''), body),
      body_uz   = coalesce(p_news->>'body_uz', body_uz),
      category  = coalesce(p_news->>'category', category),
      icon      = coalesce(nullif(p_news->>'icon',''), icon),
      link_url  = coalesce(p_news->>'link_url', link_url),
      is_pinned = coalesce((p_news->>'is_pinned')::boolean, is_pinned),
      is_active = coalesce((p_news->>'is_active')::boolean, is_active)
    where id = nid;
  end if;
  return nid;
end $$;

-- delete — admin only
create or replace function app_news_delete(p_token text, p_id uuid)
returns void language plpgsql security definer
set search_path = public, extensions
as $$
declare uid uuid; r text;
begin
  uid := _session_uid(p_token);
  if uid is null then raise exception 'auth required'; end if;
  select role into r from profiles where id = uid;
  if r <> 'admin' then raise exception 'admin only'; end if;
  delete from news where id = p_id;
end $$;

grant execute on function app_news_all(text)          to anon, authenticated;
grant execute on function app_news_upsert(text,jsonb) to anon, authenticated;
grant execute on function app_news_delete(text,uuid)  to anon, authenticated;
