import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
    } catch (err) {
      setError(err?.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ maxWidth: 520, margin: '4rem auto' }}>
      <div className="card-header">
        <h2>Login</h2>
      </div>
      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        {error && <div style={{ color: '#dc3545', marginBottom: '1rem' }}>{error}</div>}
        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <span style={{ color: '#666', fontSize: '0.9rem' }}>Don't have an account? </span>
          <button
            type="button"
            onClick={() => navigate('/register')}
            style={{
              background: 'none',
              border: 'none',
              color: '#667eea',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: '0.9rem',
            }}
          >
            Sign up
          </button>
        </div>
        <div style={{ color: '#666', marginTop: '1rem', fontSize: '0.9rem' }}>
          Default admin: <b>admin</b> / <b>admin123</b> (change via env `ADMIN_BOOTSTRAP_PASSWORD`)
          <br />
          Default demo users: <b>demo_user</b>, <b>fitness_pro</b>, <b>health_conscious</b> / <b>password</b>
        </div>
      </form>
    </div>
  )
}

export default Login


