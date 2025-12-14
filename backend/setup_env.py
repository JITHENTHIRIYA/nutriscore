#!/usr/bin/env python3
"""
Interactive script to create .env file for database configuration.
"""

import os
from pathlib import Path

def create_env_file():
    print("="*60)
    print("  NutriScore+ .env File Setup")
    print("="*60)
    print()
    
    # Get current directory
    backend_dir = Path(__file__).parent
    env_file = backend_dir / '.env'
    
    # Check if .env already exists
    if env_file.exists():
        print(f"⚠️  .env file already exists at: {env_file}")
        response = input("Do you want to overwrite it? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    print("Please enter your PostgreSQL database credentials:")
    print("(Press Enter to use defaults)")
    print()
    
    db_host = input("Database host [localhost]: ").strip() or "localhost"
    db_name = input("Database name [nutriscore]: ").strip() or "nutriscore"
    db_user = input("Database user [postgres]: ").strip() or "postgres"
    db_password = input("Database password: ").strip()
    
    if not db_password:
        print("⚠️  Warning: Empty password. Make sure PostgreSQL allows passwordless connections.")
        confirm = input("Continue anyway? [y/N]: ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    # Write .env file
    env_content = f"""DB_HOST={db_host}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        # Set permissions (Unix-like systems)
        try:
            os.chmod(env_file, 0o600)  # Read/write for owner only
        except:
            pass  # Windows doesn't support chmod
        
        print()
        print("✅ .env file created successfully!")
        print(f"   Location: {env_file}")
        print()
        print("Next steps:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Create database: createdb nutriscore")
        print("  3. Run schema: psql -d nutriscore -f ../database/schema.sql")
        print("  4. Test connection: python check_setup.py")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == '__main__':
    create_env_file()

