-- Plain Council: database schema and security rules
--
-- Who can do what:
--   public (anon key, logged out)  -> read published content only; approved claims only
--   staff, role 'clerk'            -> read everything, review claims, request new items
--   staff, role 'demo'             -> read everything, change nothing (for judges)
--   pipeline (service role key)    -> writes everything; bypasses row-level security by design

-- ---------- Types ----------
create type stage_kind      as enum ('staff_report', 'committee', 'community_council', 'board', 'city_council');
create type claim_section   as enum ('what', 'reasons', 'who_where', 'conditions', 'uncertainty', 'change');
create type claim_status    as enum ('unreviewed', 'approved', 'rejected', 'needs_rereview');
create type participation_status as enum ('decided', 'upcoming', 'open');
create type motion_kind     as enum ('amendment', 'main_item', 'other');
create type request_status  as enum ('queued', 'running', 'done', 'failed');
create type staff_role      as enum ('clerk', 'demo');

-- ---------- Staff ----------
create table staff_profiles (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  role       staff_role not null,
  name       text,
  created_at timestamptz not null default now()
);

create function is_staff() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from staff_profiles where user_id = auth.uid());
$$;

create function is_clerk() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from staff_profiles where user_id = auth.uid() and role = 'clerk');
$$;

-- ---------- Items ----------
-- Every item from recent meetings is loaded (titles, wards, status).
-- has_card = true only for items with a full plain-language card.
create table items (
  ref                text primary key,            -- e.g. '2026.EX31.2'
  title              text not null,
  wards              int[] not null default '{}', -- empty = city-wide
  city_wide          boolean not null default false,
  decision_body      text,                        -- body that currently holds or last held the item
  status_text        text,                        -- as shown by the city, e.g. 'Amended'
  item_url           text not null,
  has_card           boolean not null default false,
  source_fingerprint text,                        -- hash of the item page + documents
  source_changed     boolean not null default false,
  checked_at         timestamptz,                 -- last time a person checked the card against sources
  reading_grade      numeric(4,1),
  public_submissions int,                         -- count only; no names stored
  updated_at         timestamptz not null default now()
);

-- ---------- Stages ----------
create table stages (
  id          bigint generated always as identity primary key,
  item_ref    text not null references items (ref) on delete cascade,
  stage_order int  not null,
  kind        stage_kind not null,
  body_name   text not null,                      -- e.g. 'Executive Committee'
  stage_date  date,
  outcome     text,                               -- e.g. 'Adopted with amendments'
  amended     boolean,
  decision_text text,                             -- official text at this stage (for the redline)
  source_url  text not null,
  unique (item_ref, stage_order)
);

-- ---------- Source passages ----------
-- Public city documents split into passages with page numbers.
create table passages (
  id              bigint generated always as identity primary key,
  item_ref        text not null references items (ref) on delete cascade,
  doc_title       text not null,
  doc_url         text not null,
  doc_date        date,
  stage           stage_kind not null,
  page            int,
  text_original   text not null,                  -- shown to residents
  text_normalized text not null                   -- used for matching only
);

-- ---------- Claims (card sentences) ----------
create table claims (
  id            bigint generated always as identity primary key,
  item_ref      text not null references items (ref) on delete cascade,
  section       claim_section not null,
  sort_order    int not null default 0,
  stage         stage_kind not null,              -- every sentence is tagged with its stage
  stage_date    date,
  text_en       text not null,
  text_fr       text,
  text_zh       text,
  ai_draft      text not null,                    -- original AI text, kept for history
  passage_id    bigint references passages (id),
  quote_display text,                             -- the SOURCE span, never the AI's copy
  match_score   numeric(5,2),
  flags         jsonb not null default '[]',      -- e.g. [{"type":"loaded_language","word":"massive"}]
  status        claim_status not null default 'unreviewed',
  model         text,
  reviewed_by   uuid references auth.users (id),
  reviewed_at   timestamptz,
  created_at    timestamptz not null default now()
);

create table reviews (
  id          bigint generated always as identity primary key,
  claim_id    bigint not null references claims (id) on delete cascade,
  reviewer    uuid not null references auth.users (id) default auth.uid(),
  action      text not null check (action in ('approve', 'edit', 'reject')),
  before_text text,
  after_text  text,
  created_at  timestamptz not null default now()
);

-- ---------- "What changed" between stages ----------
create table changes (
  id          bigint generated always as identity primary key,
  item_ref    text not null references items (ref) on delete cascade,
  from_stage  stage_kind not null,
  to_stage    stage_kind not null,
  change_type text not null check (change_type in ('added', 'removed', 'changed')),
  old_text    text,
  new_text    text,
  claim_id    bigint references claims (id)       -- the plain-language sentence for this change
);

-- ---------- Votes (from the Voting Record) ----------
create table votes (
  id           bigint generated always as identity primary key,
  item_ref     text not null references items (ref) on delete cascade,
  voted_at     timestamptz,
  body_name    text not null,
  motion_type  text not null,                     -- as recorded, e.g. 'Amend Item (Additional)'
  motion_kind  motion_kind not null,              -- amendment vs main item, shown on the card
  description  text,
  result       text not null,                     -- e.g. 'Carried, 23-1'
  yes_count    int,
  no_count     int,
  absent_count int,
  source       text not null default 'Toronto Open Data: Members of Toronto City Council - Voting Record'
);

-- ---------- What happens next (from the Report Request Log) ----------
create table report_requests (
  id                 bigint generated always as identity primary key,
  item_ref           text not null references items (ref) on delete cascade,
  directive          text not null,
  status             text not null,               -- as recorded: open / closed / ongoing / due / NCF
  closed_by          text,
  report_back_timing text,
  assigned_to        text,
  source             text not null default 'Toronto Open Data: Report Request Log'
);

-- ---------- How to have a say ----------
-- 'open' is only allowed when an official page states how to take part.
create table participation (
  item_ref        text primary key references items (ref) on delete cascade,
  status          participation_status not null,
  meeting_at      timestamptz,
  meeting_place   text,
  method_text     text,
  method_url      text,
  method_source   text,                           -- official page the method was taken from
  deadline_text   text,                           -- only if quoted from an official page
  deadline_source text,
  privacy_notice  text,
  constraint open_needs_method check (status <> 'open' or (method_url is not null and method_source is not null)),
  constraint deadline_needs_source check (deadline_text is null or deadline_source is not null)
);

-- ---------- Requests to add items (from the staff screen) ----------
create table requests (
  id           bigint generated always as identity primary key,
  item_ref     text not null check (item_ref ~ '^\d{4}\.[A-Z]{2}\d+\.\d+$'),
  status       request_status not null default 'queued',
  reason       text,
  requested_by uuid references auth.users (id) default auth.uid(),
  created_at   timestamptz not null default now(),
  finished_at  timestamptz
);

-- ---------- Job runs (shown in the staff screen) ----------
create table job_runs (
  id          bigint generated always as identity primary key,
  job         text not null,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  ok          boolean,
  summary     text
);

-- ---------- Row-level security ----------
alter table staff_profiles  enable row level security;
alter table items           enable row level security;
alter table stages          enable row level security;
alter table passages        enable row level security;
alter table claims          enable row level security;
alter table reviews         enable row level security;
alter table changes         enable row level security;
alter table votes           enable row level security;
alter table report_requests enable row level security;
alter table participation   enable row level security;
alter table requests        enable row level security;
alter table job_runs        enable row level security;

-- Public city records: anyone can read
create policy "public read" on items           for select using (true);
create policy "public read" on stages          for select using (true);
create policy "public read" on passages        for select using (true);
create policy "public read" on votes           for select using (true);
create policy "public read" on report_requests for select using (true);
create policy "public read" on participation   for select using (true);

-- Claims: the public sees approved only; staff see everything
create policy "public reads approved" on claims for select using (status = 'approved' or is_staff());
create policy "clerk updates"         on claims for update using (is_clerk()) with check (is_clerk());

-- Changes: public only when the plain-language sentence is approved
create policy "public reads approved changes" on changes for select using (
  is_staff() or exists (select 1 from claims c where c.id = changes.claim_id and c.status = 'approved')
);

-- Review history: staff read, clerks write
create policy "staff read"   on reviews for select using (is_staff());
create policy "clerk insert" on reviews for insert with check (is_clerk() and reviewer = auth.uid());

-- Add-item requests: staff read, clerks create
create policy "staff read"   on requests for select using (is_staff());
create policy "clerk insert" on requests for insert with check (is_clerk() and requested_by = auth.uid());

-- Job runs and staff profiles: staff read only
create policy "staff read" on job_runs       for select using (is_staff());
create policy "own profile" on staff_profiles for select using (user_id = auth.uid());

-- No insert/update/delete policies exist for the public on any table, so those are denied.
