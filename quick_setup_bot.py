#!/usr/bin/env python3
"""Quick setup script for the team bot"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv(".env.supabase_bot")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials in .env.supabase_bot")
    sys.exit(1)

print("🔧 Setting up Supabase tables...")

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create tables
setup_sql = """
-- Enable pgvector if not already enabled
create extension if not exists vector;

-- Create documents table if not exists
create table if not exists documents (
    id uuid default gen_random_uuid() primary key,
    content text not null,
    metadata jsonb,
    embedding vector(1536),
    created_at timestamp with time zone default now()
);

-- Create index for vector similarity search
create index if not exists documents_embedding_idx on documents 
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Create authorized users table
create table if not exists authorized_users (
    telegram_id bigint primary key,
    username text,
    first_name text,
    added_by bigint not null,
    added_at timestamp with time zone default now(),
    is_active boolean default true
);
"""

try:
    # Execute SQL
    result = supabase.rpc("exec_sql", {"query": setup_sql}).execute()
    print("✅ Tables created successfully!")
except Exception as e:
    if "documents" in str(e):
        print("✅ Tables already exist!")
    else:
        print(f"⚠️  Note: {e}")
        print("You may need to run the SQL manually in Supabase dashboard")

print("\n🚀 Setup complete! Now run: python supabase_team_bot.py")
