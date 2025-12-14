# Database Setup from Scratch

## Step 1: Reset PostgreSQL Password

Since you forgot your PostgreSQL password, we need to reset it.

### Option A: Reset via Single-User Mode (Recommended)

1. **Stop PostgreSQL:**
   ```bash
   brew services stop postgresql@17
   # Or if that doesn't work:
   brew services stop postgresql
   ```

2. **Start PostgreSQL in single-user mode (no password required):**
   ```bash
   # Find your PostgreSQL data directory first
   # Common locations:
   # /opt/homebrew/var/postgresql@17
   # /usr/local/var/postgresql@17
   
   # Start in single-user mode
   /opt/homebrew/opt/postgresql@17/bin/postgres --single -D /opt/homebrew/var/postgresql@17 postgres
   
   # If that path doesn't work, try:
   # /usr/local/opt/postgresql@17/bin/postgres --single -D /usr/local/var/postgresql@17 postgres
   ```

3. **In the PostgreSQL prompt, type:**
   ```sql
   ALTER USER postgres WITH PASSWORD 'your_new_password';
   ```
   (Replace `your_new_password` with a password you'll remember)

4. **Press Ctrl+D to exit**

5. **Start PostgreSQL normally:**
   ```bash
   brew services start postgresql@17
   # Or: brew services start postgresql
   ```

### Option B: Reset via pg_hba.conf

1. **Find PostgreSQL data directory:**
   ```bash
   psql -U postgres -c "SHOW data_directory;" 2>/dev/null || echo "Check: /opt/homebrew/var/postgresql@17 or /usr/local/var/postgresql@17"
   ```

2. **Edit pg_hba.conf:**
   ```bash
   # Open the file
   nano /opt/homebrew/var/postgresql@17/pg_hba.conf
   # Or: nano /usr/local/var/postgresql@17/pg_hba.conf
   ```

3. **Find the line:**
   ```
   local   all   postgres   peer
   ```
   **Change it to:**
   ```
   local   all   postgres   trust
   ```

4. **Restart PostgreSQL:**
   ```bash
   brew services restart postgresql@17
   ```

5. **Connect and reset password:**
   ```bash
   psql -U postgres
   ```
   Then in psql:
   ```sql
   ALTER USER postgres WITH PASSWORD 'your_new_password';
   \q
   ```

6. **Change pg_hba.conf back to:**
   ```
   local   all   postgres   md5
   ```

7. **Restart PostgreSQL again:**
   ```bash
   brew services restart postgresql@17
   ```

## Step 2: Drop Existing Database (if it exists)

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql, run:
DROP DATABASE IF EXISTS nutriscore;
\q
```

## Step 3: Create Fresh Database

```bash
# Create the database
createdb -U postgres nutriscore

# Or if that asks for password:
psql -U postgres -c "CREATE DATABASE nutriscore;"
```

## Step 4: Create Tables (Run Schema)

```bash
cd /Users/abiramisaravanan/Documents/nutriscore-plus
psql -U postgres -d nutriscore -f database/schema.sql
```

Enter your new password when prompted.

## Step 5: Create .env File

```bash
cd backend
python setup_env.py
```

Or manually create `backend/.env`:
```
DB_HOST=localhost
DB_NAME=nutriscore
DB_USER=postgres
DB_PASSWORD=your_new_password
```

## Step 6: Verify Setup

```bash
cd backend
source venv/bin/activate
python check_setup.py
```

You should see:
- ✅ Database connection successful
- ✅ All 3 tables found
- ✅ Users count

## Step 7: Start the Application

1. **Start backend:**
   ```bash
   cd backend
   source venv/bin/activate
   python app.py
   ```

2. **Start frontend (new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open browser:** http://localhost:3000

## Troubleshooting

### "password authentication failed"
- Your `.env` file has the wrong password
- Run: `python backend/setup_env.py` to recreate it

### "database does not exist"
- Run: `createdb -U postgres nutriscore`

### "relation does not exist"
- Run: `psql -U postgres -d nutriscore -f database/schema.sql`

### "connection refused"
- PostgreSQL is not running
- Start it: `brew services start postgresql@17`

