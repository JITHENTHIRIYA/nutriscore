#!/usr/bin/env python3
"""
Quick diagnostic script to check if database connection and setup are working.
Run this before starting the Flask server.
"""

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'nutriscore'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

def dsn_from_env():
    return (
        f"host={DB_CONFIG['host']} "
        f"dbname={DB_CONFIG['database']} "
        f"user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )

print("="*60)
print("NutriScore+ Database Connection Check")
print("="*60)
print(f"Host: {DB_CONFIG['host']}")
print(f"Database: {DB_CONFIG['database']}")
print(f"User: {DB_CONFIG['user']}")
print(f"Password: {'*' * len(DB_CONFIG['password']) if DB_CONFIG['password'] else '(empty)'}")
print("="*60)

# Check if .env file exists
if not os.path.exists('.env'):
    print("⚠️  WARNING: .env file not found!")
    print("   Create a .env file in the backend/ directory with:")
    print("   DB_HOST=localhost")
    print("   DB_NAME=nutriscore")
    print("   DB_USER=postgres")
    print("   DB_PASSWORD=your_password")
    print()
else:
    print("✅ .env file found")

# Try to connect
try:
    print("\nAttempting database connection...")
    conn = psycopg.connect(dsn_from_env())
    print("✅ Database connection successful!")
    
    # Check if tables exist
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'food_items', 'consumption')
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"\n📊 Found {len(tables)} required tables:")
        for table in tables:
            print(f"   ✅ {table[0]}")
        
        if len(tables) < 3:
            print("\n⚠️  WARNING: Some tables are missing!")
            print("   Run: psql -d nutriscore -f ../database/schema.sql")
        
        # Check if users table has data
        cur.execute("SELECT COUNT(*) FROM users;")
        user_count = cur.fetchone()[0]
        print(f"\n👥 Users in database: {user_count}")
        
        if user_count == 0:
            print("   ℹ️  No users found. You can create users via the API or frontend.")
        else:
            cur.execute("SELECT user_id, username FROM users LIMIT 5;")
            users = cur.fetchall()
            print("   Sample users:")
            for user in users:
                print(f"      - {user[1]} (ID: {user[0]})")
    
    conn.close()
    print("\n✅ All checks passed! You can start the Flask server.")
    
except psycopg.OperationalError as e:
    print(f"\n❌ Database connection failed!")
    print(f"   Error: {e}")
    print("\n💡 Common issues:")
    print("   1. PostgreSQL is not running")
    print("   2. Database 'nutriscore' doesn't exist")
    print("   3. Wrong credentials in .env file")
    print("   4. PostgreSQL is not listening on localhost")
    print("\n   Try:")
    print("   - Start PostgreSQL: brew services start postgresql (macOS)")
    print("   - Create database: createdb nutriscore")
    print("   - Check .env file has correct credentials")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"   Type: {type(e).__name__}")

print("="*60)

