# Migration Guide: Food Ownership Tracking

## Overview
This migration adds ownership tracking to the `food_items` table, allowing users to create food items and only edit/delete their own items (admins can edit/delete any).

## Migration Steps

### 1. Run the Migration SQL
Execute the migration script to add the `created_by_user_id` column:

```bash
# Using psql
psql -h localhost -U postgres -d nutriscore -f database/migration_add_food_ownership.sql

# Or using your database client
# Open database/migration_add_food_ownership.sql and run it
```

### 2. Verify Migration
Check that the column was added:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'food_items' AND column_name = 'created_by_user_id';
```

### 3. Restart Backend
After running the migration, restart your Flask backend:

```bash
cd backend
python app.py
```

## What Changed

### Database
- Added `created_by_user_id` column to `food_items` table
- Added index for faster ownership queries
- Existing food items will have `created_by_user_id = NULL` (system/imported foods)

### Backend API
- **POST /api/foods**: Now allows all authenticated users (was admin-only)
- **PUT /api/foods/<id>**: Users can only edit their own foods (admins can edit any)
- **DELETE /api/foods/<id>**: Users can only delete their own foods (admins can delete any)
- All endpoints now return `created_by_user_id` in responses

### Frontend
- "Add Food" button now visible to all authenticated users
- Edit/Delete buttons only shown for:
  - Foods created by the current user, OR
  - All foods if user is admin
- Read-only indicator for foods created by other users

## Notes
- Food names remain globally unique (Option A)
- Users cannot edit/delete foods created by other users (unless admin)
- System/imported foods (NULL created_by_user_id) can only be edited/deleted by admins

