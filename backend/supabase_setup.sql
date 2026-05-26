-- Run this in Supabase SQL Editor to set up Fitcheck Phase 1

-- Users profile table (mirrors auth.users)
create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text,
  avatar_url text,
  subscription_tier text not null default 'free' check (subscription_tier in ('free', 'pro')),
  created_at timestamptz not null default now()
);

-- Auto-create user profile on sign-up
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.users (id, email, display_name)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'display_name'
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Catalog items table
create table if not exists public.catalog_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  name text not null,
  category text not null check (category in ('top','bottom','shoes','accessories','outerwear')),
  colors text[] not null default '{}',
  brand text,
  size text,
  seasons text[] not null default '{}',
  style_tags text[] not null default '{}',
  fit_type text,
  image_url text,
  image_url_original text,
  is_favorite boolean not null default false,
  notes text,
  created_at timestamptz not null default now()
);

-- Row Level Security: users can only access their own items
alter table public.catalog_items enable row level security;

create policy "Users see own items" on public.catalog_items
  for select using (auth.uid() = user_id);

create policy "Users insert own items" on public.catalog_items
  for insert with check (auth.uid() = user_id);

create policy "Users update own items" on public.catalog_items
  for update using (auth.uid() = user_id);

create policy "Users delete own items" on public.catalog_items
  for delete using (auth.uid() = user_id);

-- Storage bucket for catalog images (run in Supabase Storage UI or here)
-- insert into storage.buckets (id, name, public) values ('catalog', 'catalog', true);
