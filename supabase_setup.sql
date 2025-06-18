-- Supabase Vector Store Setup for T2T2 Team Bot
-- Run this in your Supabase SQL editor

-- Enable pgvector extension
create extension if not exists vector;

-- Create documents table for vector storage
create table if not exists documents (
    id uuid default gen_random_uuid() primary key,
    content text not null,
    metadata jsonb default '{}'::jsonb,
    embedding vector(1536),
    collection_name text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create indexes for performance
create index if not exists documents_embedding_idx 
on documents using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

create index if not exists documents_collection_idx 
on documents(collection_name);

create index if not exists documents_metadata_idx 
on documents using gin(metadata);

-- Create function for similarity search per collection
create or replace function match_documents(
    query_embedding vector(1536),
    match_count int default 5,
    collection text default '',
    filter jsonb default '{}'::jsonb
) returns table (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
) 
language plpgsql
as $$
begin
    return query
    select
        d.id,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) as similarity
    from documents d
    where 
        (collection = '' or d.collection_name = collection) and
        (filter = '{}'::jsonb or d.metadata @> filter)
    order by d.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- Create function for each user's collection (template)
-- The bot will create these dynamically for each user
create or replace function create_user_match_function(user_collection text)
returns void
language plpgsql
as $$
declare
    func_name text;
begin
    func_name := 'match_' || user_collection;
    
    execute format('
        create or replace function %I(
            query_embedding vector(1536),
            match_count int default 5
        ) returns table (
            id uuid,
            content text,
            metadata jsonb,
            similarity float
        ) 
        language plpgsql
        as $func$
        begin
            return query
            select * from match_documents(
                query_embedding,
                match_count,
                %L,
                ''{}''::jsonb
            );
        end;
        $func$
    ', func_name, user_collection);
end;
$$;

-- Create RLS (Row Level Security) policies for additional security
alter table documents enable row level security;

-- Policy: Service role has full access
create policy "Service role has full access to documents" on documents
    for all
    to service_role
    using (true)
    with check (true);

-- Create audit table for tracking user actions
create table if not exists user_actions (
    id uuid default gen_random_uuid() primary key,
    user_id text not null,
    action text not null,
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Index for user actions
create index if not exists user_actions_user_id_idx on user_actions(user_id);
create index if not exists user_actions_created_at_idx on user_actions(created_at desc);

-- Grant permissions (adjust based on your needs)
grant usage on schema public to anon, authenticated;
grant select on documents to anon, authenticated;
grant all on documents to service_role;
grant all on user_actions to service_role;