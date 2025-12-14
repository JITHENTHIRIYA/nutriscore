-- Migration: Add ownership tracking to food_items
-- Date: 2025-12-14
-- Purpose: Allow users to create food items and track ownership
--          Users can only edit/delete their own food items (admins can edit/delete any)

-- Add created_by_user_id column to food_items table
ALTER TABLE food_items 
ADD COLUMN created_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

-- Create index for faster ownership queries
CREATE INDEX idx_food_items_created_by ON food_items(created_by_user_id);

-- Add comment
COMMENT ON COLUMN food_items.created_by_user_id IS 'User who created this food item. NULL for system/imported foods.';

