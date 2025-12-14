# NutriScore+ - Nutrition Tracking System

A comprehensive web application for tracking daily nutrition, analyzing dietary intake, and achieving health goals. Built with Flask (Python) backend and React frontend, using PostgreSQL database.

## Project Overview

NutriScore+ helps users:
- Track daily food consumption
- Monitor nutritional intake (calories, protein, carbs, fat, fiber, sugars)
- Calculate health scores for meals
- Analyze dietary patterns with visualizations
- Set and track dietary goals

## Tech Stack

### Backend
- **Flask 3.0** - Python web framework
- **PostgreSQL** - Relational database
- **psycopg v3** - PostgreSQL adapter
- **Flask-CORS** - Cross-origin resource sharing

### Frontend
- **React 18** - UI framework
- **React Router** - Navigation
- **Recharts** - Data visualization
- **Vite** - Build tool
- **Axios** - HTTP client

### Database
- **PostgreSQL** with comprehensive schema
- 3 main tables: users, food_items, consumption
- 4 analytical views for reporting
- 11 indexes for performance optimization

## Project Structure

```
nutriscore-plus/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── venv/               # Virtual environment
├── database/
│   ├── schema.sql          # Database schema
│   └── load_data.py        # ETL script for loading CSV data
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api.js          # API client
│   │   └── App.jsx         # Main app
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Setup Instructions

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb nutriscore

# Run schema
psql -d nutriscore -f database/schema.sql

# Load food data (update path in load_data.py first)
python database/load_data.py
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
# DB_HOST=localhost
# DB_NAME=nutriscore
# DB_USER=postgres
# DB_PASSWORD=your_password

# Run server
python app.py
```

Backend runs on http://127.0.0.1:5000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs on http://localhost:3000

## API Endpoints

### Health
- `GET /api/health` - Health check

### Users
- `GET /api/users` - List all users
- `GET /api/users/<id>` - Get user with stats
- `POST /api/users` - Create user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

### Foods
- `GET /api/foods` - List foods (with search/category filters)
- `GET /api/foods/<id>` - Get food item
- `POST /api/foods` - Create food
- `PUT /api/foods/<id>` - Update food
- `DELETE /api/foods/<id>` - Delete food

### Consumption
- `GET /api/consumption?user_id=X&date=Y` - Get consumption entries
- `GET /api/consumption/<id>` - Get entry
- `POST /api/consumption` - Log consumption
- `PUT /api/consumption/<id>` - Update entry
- `DELETE /api/consumption/<id>` - Delete entry

### Analytics
- `GET /api/analytics/category-nutrition` - Average nutrition by category
- `GET /api/analytics/top-foods?limit=20` - Top nutritious foods
- `GET /api/analytics/user-progress/<id>?days=30` - User progress over time
- `GET /api/analytics/meal-distribution?user_id=X&days=30` - Meal type distribution
- `GET /api/analytics/popular-foods?user_id=X` - Most consumed foods

## Features

### ✅ Completed
- Complete database schema with constraints
- Data loading pipeline (550+ food items)
- Full CRUD API for all entities
- Health score calculation
- 5 analytical visualizations
- Modern, responsive UI
- User management
- Food catalog with search/filter
- Consumption logging
- Real-time analytics dashboard

### 📊 Visualizations
1. **Average Nutrition by Category** - Bar chart showing macronutrients per category
2. **Top Nutritious Foods** - Table of top 20 foods by health score
3. **User Progress Over Time** - Line chart tracking daily calories and health scores
4. **Meal Type Distribution** - Pie chart showing meal breakdown
5. **Most Consumed Foods** - Popular foods tracking

## Health Score Calculation

Health score formula: `50 + (Protein/Calories)*100 + (Fiber-Sugars)*2`
- Clamped to 0-100 range
- Higher scores indicate healthier food choices
- Automatically calculated for consumption entries

## Database Schema

### Tables
- **users**: User accounts with dietary goals
- **food_items**: Master catalog of foods (550+ items)
- **consumption**: Daily food consumption logs

### Views
- **daily_summary**: Aggregated daily nutrition per user
- **food_popularity**: Most consumed foods with stats
- **user_progress**: Overall user statistics
- **category_distribution**: Food category breakdown

## Team Members

- Harish Suresh - Database schema, CRUD operations, Flask API
- Jithenthiriya C. Kathirvel - Food items table, ETL pipeline, analytical views
- Abirami Saravanan - Consumption table, constraints, health score logic

## License

This project is part of a database systems course assignment.

