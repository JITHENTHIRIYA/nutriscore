-- ============================================================
-- NutriScore+ Database Schema
-- Authors: Harish Suresh, Jithenthiriya C. Kathirvel, Abirami Saravanan
-- Date: November 2025
-- Dataset: Food Nutrition Dataset (Kaggle)
-- ============================================================

-- Author: Abirami Saravanan
-- Clean slate - drop existing tables
DROP TABLE IF EXISTS consumption CASCADE;
DROP TABLE IF EXISTS food_items CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- PART 1: TABLE DEFINITIONS
-- ============================================================

-- Users Table
-- Author: Harish Suresh
-- Purpose: Store user information and dietary preferences
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'user'
        CHECK (role IN ('admin', 'user')),
    -- Profile fields (goal + auto-calculated calories)
    height_value NUMERIC(10,2),
    height_unit VARCHAR(10) DEFAULT 'cm' CHECK (height_unit IN ('cm', 'in')),
    weight_value NUMERIC(10,2),
    weight_unit VARCHAR(10) DEFAULT 'kg' CHECK (weight_unit IN ('kg', 'lb')),
    dietary_goal VARCHAR(50) DEFAULT 'maintain'
        CHECK (dietary_goal IN ('weight_gain', 'weight_loss', 'maintain', 'eat_healthy')),
    target_calories INTEGER DEFAULT 2000 CHECK (target_calories >= 1200 AND target_calories <= 4000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints for data integrity
    CONSTRAINT username_not_empty CHECK (LENGTH(TRIM(username)) > 0)
);

-- User Profile Change Log (audit)
CREATE TABLE IF NOT EXISTS user_profile_changes (
    change_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    changed_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    changed_by_role VARCHAR(20),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_fields JSONB NOT NULL
);

-- Food Items Table
-- Author: Jithenthiriya C. Kathirvel  
-- Purpose: Store unique food items from the dataset
CREATE TABLE food_items (
    food_id SERIAL PRIMARY KEY,
    food_name VARCHAR(200) NOT NULL UNIQUE,
    calories NUMERIC(10,2) NOT NULL CHECK (calories >= 0),
    protein NUMERIC(10,2) NOT NULL CHECK (protein >= 0),
    carbs NUMERIC(10,2) NOT NULL CHECK (carbs >= 0),
    fat NUMERIC(10,2) NOT NULL CHECK (fat >= 0),
    fiber NUMERIC(10,2) NOT NULL CHECK (fiber >= 0),
    sugars NUMERIC(10,2) NOT NULL CHECK (sugars >= 0),
    nutrition_density NUMERIC(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Data integrity constraints
    CONSTRAINT food_name_not_empty CHECK (LENGTH(TRIM(food_name)) > 0),
    CONSTRAINT valid_macros CHECK (protein + carbs + fat >= 0)
);

-- Consumption Table
-- Author: Abirami Saravanan
-- Purpose: Track user's daily food consumption
CREATE TABLE consumption (
    entry_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES food_items(food_id) ON DELETE RESTRICT,
    date DATE NOT NULL,
    portion_size NUMERIC(10,2) DEFAULT 1.0 CHECK (portion_size > 0),
    calories NUMERIC(10,2) NOT NULL CHECK (calories >= 0),
    protein NUMERIC(10,2) NOT NULL CHECK (protein >= 0),
    carbs NUMERIC(10,2) NOT NULL CHECK (carbs >= 0),
    fat NUMERIC(10,2) NOT NULL CHECK (fat >= 0),
    fiber NUMERIC(10,2) NOT NULL CHECK (fiber >= 0),
    sugars NUMERIC(10,2) NOT NULL CHECK (sugars >= 0),
    health_score INTEGER CHECK (health_score >= 0 AND health_score <= 100),
    meal_type VARCHAR(20) CHECK (meal_type IN ('Breakfast', 'Lunch', 'Dinner', 'Snack')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_date CHECK (date <= CURRENT_DATE),
    CONSTRAINT valid_entry CHECK (calories > 0 OR protein > 0 OR carbs > 0 OR fat > 0)
);

-- ============================================================
-- PART 2: INDEXES FOR PERFORMANCE
-- ============================================================

-- Author: Harish Suresh
-- Purpose: Speed up common queries

-- User indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_dietary_goal ON users(dietary_goal);

-- Food item indexes
CREATE INDEX idx_food_items_name ON food_items(food_name);
CREATE INDEX idx_food_items_calories ON food_items(calories);

-- Consumption indexes (most queried table)
CREATE INDEX idx_consumption_user_date ON consumption(user_id, date DESC);
CREATE INDEX idx_consumption_date ON consumption(date DESC);
CREATE INDEX idx_consumption_food ON consumption(food_id);
CREATE INDEX idx_consumption_health_score ON consumption(health_score DESC);
CREATE INDEX idx_consumption_meal_type ON consumption(meal_type);

-- ============================================================
-- PART 3: SAMPLE DATA
-- ============================================================

-- Author: Jithenthiriya C. Kathirvel
-- Purpose: Create demo users for testing

INSERT INTO users (username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit) VALUES
('admin', 'admin', 'maintain', 2000, 170, 'cm', 70, 'kg'),
('demo_user', 'user', 'maintain', 2000, 170, 'cm', 70, 'kg'),
('fitness_pro', 'user', 'weight_gain', 2400, 180, 'cm', 80, 'kg'),
('health_conscious', 'user', 'eat_healthy', 2000, 165, 'cm', 60, 'kg');

-- Note: Food items will be populated from CSV using load_data.py
-- Sample consumption entries will also be created by the script

-- ============================================================
-- PART 4: VIEWS FOR ANALYTICS
-- ============================================================

-- Daily Summary View
-- Author: Jithenthiriya C. Kathirvel
-- Purpose: Aggregate daily nutrition totals per user
CREATE OR REPLACE VIEW daily_summary AS
SELECT 
    c.user_id,
    u.username,
    c.date,
    COUNT(*) as meals_count,
    ROUND(SUM(c.calories)::NUMERIC, 2) as total_calories,
    ROUND(SUM(c.protein)::NUMERIC, 2) as total_protein,
    ROUND(SUM(c.carbs)::NUMERIC, 2) as total_carbs,
    ROUND(SUM(c.fat)::NUMERIC, 2) as total_fat,
    ROUND(SUM(c.fiber)::NUMERIC, 2) as total_fiber,
    ROUND(SUM(c.sugars)::NUMERIC, 2) as total_sugars,
    ROUND(AVG(c.health_score)::NUMERIC, 0) as avg_health_score,
    u.target_calories,
    u.dietary_goal
FROM consumption c
JOIN users u ON c.user_id = u.user_id
GROUP BY c.user_id, u.username, c.date, u.target_calories, u.dietary_goal
ORDER BY c.date DESC;

-- Food Popularity View
-- Author: Harish Suresh
-- Purpose: Track most consumed foods
CREATE OR REPLACE VIEW food_popularity AS
SELECT 
    f.food_id,
    f.food_name,
    COUNT(c.entry_id) as times_consumed,
    ROUND(AVG(c.health_score)::NUMERIC, 0) as avg_health_score,
    ROUND(f.calories::NUMERIC, 2) as calories,
    ROUND(f.protein::NUMERIC, 2) as protein
FROM food_items f
LEFT JOIN consumption c ON f.food_id = c.food_id
GROUP BY f.food_id, f.food_name, f.calories, f.protein
ORDER BY times_consumed DESC;

-- User Progress View
-- Author: Abirami Saravanan
-- Purpose: Track user's overall progress
CREATE OR REPLACE VIEW user_progress AS
SELECT 
    u.user_id,
    u.username,
    u.dietary_goal,
    u.target_calories,
    COUNT(DISTINCT c.date) as days_tracked,
    COUNT(c.entry_id) as total_entries,
    ROUND(AVG(c.calories)::NUMERIC, 2) as avg_daily_calories,
    ROUND(AVG(c.protein)::NUMERIC, 2) as avg_daily_protein,
    ROUND(AVG(c.health_score)::NUMERIC, 0) as avg_health_score,
    MAX(c.date) as last_entry_date
FROM users u
LEFT JOIN consumption c ON u.user_id = c.user_id
GROUP BY u.user_id, u.username, u.dietary_goal, u.target_calories;

-- Daily Health Score View (daily average health score per user)
CREATE OR REPLACE VIEW daily_health_score AS
SELECT
    user_id,
    date,
    ROUND(AVG(health_score)::NUMERIC, 2) AS daily_health_score,
    COUNT(*) AS entries_count
FROM consumption
GROUP BY user_id, date
ORDER BY date DESC;

-- Overall Health Score View (overall average health score per user)
CREATE OR REPLACE VIEW overall_health_score AS
SELECT
    user_id,
    ROUND(AVG(health_score)::NUMERIC, 2) AS overall_health_score,
    COUNT(*) AS entries_count,
    COUNT(DISTINCT date) AS days_tracked
FROM consumption
GROUP BY user_id;

-- Food Distribution View (removed category, now shows by food_id)
-- Author: Harish Suresh
-- Purpose: Show food distribution breakdown
CREATE OR REPLACE VIEW food_distribution AS
SELECT 
    c.user_id,
    u.username,
    f.food_id,
    f.food_name,
    COUNT(*) as count,
    ROUND(SUM(c.calories)::NUMERIC, 2) as total_calories,
    ROUND(AVG(c.health_score)::NUMERIC, 0) as avg_score
FROM consumption c
JOIN users u ON c.user_id = u.user_id
JOIN food_items f ON c.food_id = f.food_id
GROUP BY c.user_id, u.username, f.food_id, f.food_name
ORDER BY c.user_id, count DESC;

-- ============================================================
-- PART 5: ANALYTICAL QUERIES (FOR TESTING)
-- ============================================================

-- Query 1: Top 10 Healthiest Foods
-- Author: Harish Suresh
-- Purpose: Find foods with best health scores
-- SELECT food_name, category, avg_health_score, times_consumed
-- FROM food_popularity
-- WHERE times_consumed > 0
-- ORDER BY avg_health_score DESC
-- LIMIT 10;

-- Query 2: User Daily Progress
-- Author: Jithenthiriya C. Kathirvel
-- Purpose: Show daily nutrition for a user
-- SELECT date, meals_count, total_calories, target_calories,
--        (total_calories - target_calories) as difference,
--        total_protein, avg_health_score
-- FROM daily_summary
-- WHERE user_id = 1
-- ORDER BY date DESC;

-- Query 3: Category Breakdown
-- Author: Abirami Saravanan
-- Purpose: Show food category distribution
-- SELECT category, count, avg_score
-- FROM category_distribution
-- WHERE user_id = 1
-- ORDER BY count DESC;

-- Query 4: Weekly Trends
-- Author: Harish Suresh
-- Purpose: Show weekly averages
-- SELECT 
--     DATE_TRUNC('week', date) as week,
--     COUNT(DISTINCT date) as days_logged,
--     ROUND(AVG(total_calories)::NUMERIC, 2) as avg_calories,
--     ROUND(AVG(total_protein)::NUMERIC, 2) as avg_protein,
--     ROUND(AVG(avg_health_score)::NUMERIC, 0) as avg_score
-- FROM daily_summary
-- WHERE user_id = 1
-- GROUP BY week
-- ORDER BY week DESC;

-- ============================================================
-- PART 6: DATA VALIDATION QUERIES
-- ============================================================

-- Verify table creation
-- SELECT 'Users' as table_name, COUNT(*) as count FROM users
-- UNION ALL
-- SELECT 'Food Items', COUNT(*) FROM food_items
-- UNION ALL
-- SELECT 'Consumption', COUNT(*) FROM consumption;

-- Display sample data
-- SELECT * FROM users;
-- SELECT * FROM food_items LIMIT 10;
-- SELECT * FROM daily_summary LIMIT 10;

COMMENT ON TABLE users IS 'Stores user accounts and dietary preferences';
COMMENT ON TABLE food_items IS 'Master list of foods from nutrition dataset';
COMMENT ON TABLE consumption IS 'Daily food consumption logs';
COMMENT ON COLUMN consumption.health_score IS 'Calculated score: 70 + 50 * (Protein/Calories) + 5 * Fiber - 2.5 * Sugars';
COMMENT ON COLUMN consumption.portion_size IS 'Multiplier for nutrition values (default 1.0)';