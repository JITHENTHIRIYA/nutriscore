#!/bin/bash
# Migration script to add food ownership tracking
# Usage: ./run_migration.sh [database_name] [username]

DB_NAME=${1:-nutriscore}
DB_USER=${2:-postgres}

echo "Running migration to add created_by_user_id column to food_items table..."
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f "$(dirname "$0")/migration_add_food_ownership.sql"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Migration completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Restart your backend server"
    echo "2. Refresh your frontend application"
else
    echo ""
    echo "✗ Migration failed. Please check the error above."
    echo ""
    echo "Note: If you see 'column already exists', the migration has already been run."
fi

