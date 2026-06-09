-- ============================================================================
-- PROJECT FILE ATTACHMENTS (up to 10 MB). Stored in a Supabase Storage bucket
-- (not base64 in a column). projects.files holds [{url,name,size}, ...].
-- ============================================================================
alter table projects add column if not exists files jsonb default '[]'::jsonb;

-- Storage bucket: public read, 10 MB per-file cap. allowed_mime_types = null
-- (any type) — the client validates extension + size; the hard cap is here.
insert into storage.buckets (id, name, public, file_size_limit)
values ('project-files', 'project-files', true, 10485760)
on conflict (id) do update set public = true, file_size_limit = 10485760;

-- Policies on storage.objects for this bucket (anon path = the public client).
drop policy if exists "project_files_read"   on storage.objects;
drop policy if exists "project_files_insert" on storage.objects;
create policy "project_files_read" on storage.objects
  for select to anon, authenticated using (bucket_id = 'project-files');
create policy "project_files_insert" on storage.objects
  for insert to anon, authenticated with check (bucket_id = 'project-files');
