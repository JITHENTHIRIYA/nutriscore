# Run Migration to Enable Food Ownership

## Problem
You can add food items, but you can't edit or delete them because the ownership tracking column hasn't been added to the database yet.

## Solution: Run the Migration

### Option 1: Using psql (Recommended)

```bash
# Navigate to the project directory
cd /Users/abiramisaravanan/Documents/nutriscore-plus

# Run the migration (you'll be prompted for your PostgreSQL password)
psql -h localhost -U postgres -d nutriscore -f database/migration_add_food_ownership.sql
```

### Option 2: Using the migration script

```bash
cd /Users/abiramisaravanan/Documents/nutriscore-plus/database
./run_migration.sh
```

### Option 3: Using a Database GUI Tool

1. Open your PostgreSQL client (pgAdmin, DBeaver, TablePlus, etc.)
2. Connect to your `nutriscore` database
3. Open and run the file: `database/migration_add_food_ownership.sql`

## After Running the Migration

1. **Restart your backend server** (if it's running):
   ```bash
   # Stop the current backend (Ctrl+C)
   # Then restart it
   cd backend
   python app.py
   ```

2. **Refresh your frontend** - The food items you created should now show Edit/Delete buttons

## Verify Migration Worked

After running the migration, you should be able to:
- ✅ Edit food items you created
- ✅ Delete food items you created
- ✅ See "Read-only" for food items created by others (unless you're admin)

## Note

Foods created **before** running the migration will have `created_by_user_id = NULL` and can only be edited/deleted by admins. Foods created **after** the migration will be properly tracked.

