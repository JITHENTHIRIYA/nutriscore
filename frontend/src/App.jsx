import React, { useEffect, useMemo, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate, Navigate } from 'react-router-dom'
import Users from './components/Users'
import Foods from './components/Foods'
import Consumption from './components/Consumption'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import Register from './components/Register'
import Onboarding from './components/Onboarding'
import Profile from './components/Profile'
import './App.css'
import { AuthProvider, useAuth } from './auth/AuthContext'

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppShell />
      </Router>
    </AuthProvider>
  )
}

function AppShell() {
  const { user, loading } = useAuth()

  if (loading) return <div className="card">Loading…</div>

  // Not logged in: show login or register
  if (!user) {
    return (
      <div className="app">
        <main className="main-content">
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Login />} />
          </Routes>
        </main>
      </div>
    )
  }

  // Logged in but profile incomplete: show onboarding
  if (!user.profile_complete) {
    return (
      <div className="app">
        <main className="main-content">
          <Routes>
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="*" element={<Navigate to="/onboarding" replace />} />
          </Routes>
        </main>
      </div>
    )
  }

  // Logged in with complete profile: show app
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          {/* Admin-only routes (UI hidden for users too) */}
          {user.role === 'admin' && <Route path="/users" element={<Users />} />}
          <Route path="/foods" element={<Foods />} />
          {user.role !== 'admin' && <Route path="/consumption" element={<Consumption />} />}
          {/* Fallback */}
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  )
}

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState(window.location.pathname)

  const tabs = useMemo(() => {
    if (!user) return []
    if (user.role === 'admin') {
      return [
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/foods', label: 'Food Catalog' },
        { path: '/profile', label: 'Profile' },
        { path: '/users', label: 'Users' },
      ]
    }
    return [
      { path: '/dashboard', label: 'Dashboard' },
      { path: '/consumption', label: 'Log Food' },
      { path: '/foods', label: 'Food Catalog' },
      { path: '/profile', label: 'Profile' },
    ]
  }, [user])

  const handleNav = (path) => {
    setActiveTab(path)
    navigate(path)
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>🍎 NutriScore+</h1>
      </div>
      <div className="navbar-links">
        {tabs.map((t) => (
          <button
            key={t.path}
            className={activeTab === t.path || (t.path === '/dashboard' && activeTab === '/') ? 'active' : ''}
            onClick={() => handleNav(t.path)}
          >
            {t.label}
          </button>
        ))}
        <button
          className="btn btn-secondary"
          style={{ 
            marginLeft: '1rem', 
            padding: '0.5rem 1rem', 
            fontSize: '0.9rem',
            backgroundColor: '#dc3545',
            color: 'white',
            border: '2px solid #c82333',
            fontWeight: 'bold',
            boxShadow: '0 2px 4px rgba(220, 53, 69, 0.3)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#c82333'
            e.currentTarget.style.transform = 'scale(1.05)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#dc3545'
            e.currentTarget.style.transform = 'scale(1)'
          }}
          onClick={async () => {
            await logout()
            navigate('/')
          }}
        >
          Logout
        </button>
      </div>
    </nav>
  )
}

export default App

