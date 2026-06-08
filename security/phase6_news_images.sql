-- ============================================================================
-- NEWS IMAGES. Add an image to a news item. The image is uploaded by the admin,
-- compressed client-side and stored as a data URL in image_url (so it flows
-- through the admin-only app_news_upsert RPC — no public storage bucket needed).
-- ============================================================================
alter table news add column if not exists image_url text;

-- extend the admin upsert to persist image_url
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
    insert into news(title, title_uz, body, body_uz, category, icon, link_url, image_url, is_pinned, is_active)
    values (p_news->>'title', nullif(p_news->>'title_uz',''), p_news->>'body', nullif(p_news->>'body_uz',''),
            nullif(p_news->>'category',''), coalesce(nullif(p_news->>'icon',''),'📰'),
            nullif(p_news->>'link_url',''), nullif(p_news->>'image_url',''),
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
      image_url = coalesce(p_news->>'image_url', image_url),
      is_pinned = coalesce((p_news->>'is_pinned')::boolean, is_pinned),
      is_active = coalesce((p_news->>'is_active')::boolean, is_active)
    where id = nid;
  end if;
  return nid;
end $$;
grant execute on function app_news_upsert(text,jsonb) to anon, authenticated;
