# NutriScore+ Frontend

React-based web application for nutrition tracking with comprehensive analytics and visualizations.

## Features

- **User Management**: Create, view, update, and delete user accounts
- **Food Catalog**: Browse, search, and manage food items with full nutritional information
- **Consumption Logging**: Log daily food consumption with automatic nutrition calculation
- **Analytics Dashboard**: 5 comprehensive visualizations:
  - Average Nutrition by Category (Bar Chart)
  - Top 20 Most Nutritious Foods
  - User Progress Over Time (Line Chart)
  - Meal Type Distribution (Pie Chart)
  - Most Consumed Foods

## Setup

### Prerequisites

- Node.js 16+ and npm
- Backend API running on http://127.0.0.1:5000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
npm run build
```

## Tech Stack

- **React 18** - UI framework
- **React Router** - Navigation
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Vite** - Build tool

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Users.jsx          # User management
│   │   ├── Foods.jsx          # Food catalog
│   │   ├── Consumption.jsx   # Consumption logging
│   │   └── Dashboard.jsx     # Analytics dashboard
│   ├── api.js                 # API client
│   ├── App.jsx               # Main app component
│   ├── App.css               # Styles
│   ├── main.jsx             # Entry point
│   └── index.css            # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## API Integration

The frontend connects to the Flask backend API at `/api`. All API calls are handled through the `api.js` module.

## Features in Detail

### User Management
- Create users with dietary goals (balanced, highProtein, lowSugar, lowCarb)
- Set custom calorie targets
- View user statistics and progress

### Food Catalog
- Search foods by name
- Filter by category
- View complete nutritional profiles
- Add/edit/delete food items

### Consumption Logging
- Log food consumption with portion sizes
- Automatic nutrition calculation
- Health score calculation
- Filter by date and meal type
- View daily nutrition totals

### Analytics Dashboard
- Real-time data visualization
- User-specific and global analytics
- Interactive charts with tooltips
- Progress tracking over time

