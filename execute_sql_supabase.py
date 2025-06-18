#!/usr/bin/env python3
"""Execute SQL on Supabase using direct PostgreSQL connection"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv('.env.supabase_bot')

# Parse the DATABASE_URL from Supabase
database_url = os.getenv('DATABASE_URL')
if not database_url:
    # Construct from Supabase URL
    supabase_url = os.getenv('SUPABASE_URL')
    # Extract project ref from URL
    project_ref = supabase_url.split('//')[1].split('.')[0]
    
    # Typical Supabase database URL format
    database_url = f"postgresql://postgres.{project_ref}:postgres@{project_ref}.supabase.co:6543/postgres"
    print(f"⚠️  No DATABASE_URL found, constructed: {database_url}")
    print("   Add DATABASE_URL to .env.supabase_bot for direct SQL access")
    exit(1)

# Read SQL file
with open('add_user_sessions_table.sql', 'r') as f:
    sql = f.read()

print("📝 Executing SQL to create user_sessions table...")

try:
    # Parse database URL
    result = urlparse(database_url)
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    
    # Execute SQL
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    
    print("✅ Successfully created user_sessions table!")
    
    # Verify table exists
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'user_sessions'
        ORDER BY ordinal_position;
    """)
    
    print("\n📋 Table structure:")
    for col in cur.fetchall():
        print(f"   - {col[0]}: {col[1]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 To add the table manually:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the contents of add_user_sessions_table.sql")
    print("4. Click 'Run'")