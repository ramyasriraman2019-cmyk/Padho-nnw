-- Padho! database for Supabase. Paste into SQL Editor and press Run (safe to run twice).

create table if not exists students (
  id text primary key,
  name text not null,
  roll text,
  class_name text,
  section text,
  language text,
  level integer default 1,
  photo text,
  consent integer default 0,
  teacher text,
  created_at text
);

create table if not exists attempts (
  id text primary key,
  student_id text not null,
  ts text,
  language text,
  level integer,
  wcpm double precision,
  accuracy double precision,
  coverage double precision,
  correct integer,
  misread integer,
  skipped integer,
  extra integer,
  duration double precision,
  comprehension integer default -1,
  met integer default 0,
  bad_words text,
  skip_words text
);
create index if not exists ix_attempts_student on attempts(student_id);

create table if not exists badges (
  id text primary key,
  student_id text not null,
  badge_key text not null,
  earned_at text
);

-- The app talks to these tables only from the server, using the service_role key.
-- Turning on row level security blocks anyone who finds the public anon key.
alter table students enable row level security;
alter table attempts enable row level security;
alter table badges   enable row level security;
