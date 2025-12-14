import React, { useState, useEffect } from 'react'
import { usersAPI } from '../api'

const GOALS = [
  { value: 'weight_loss', label: 'weight_loss' },
  { value: 'maintain', label: 'maintain' },
  { value: 'eat_healthy', label: 'eat_healthy' },
  { value: 'weight_gain', label: 'weight_gain' },
]

function calcTargetLocal({ height_value, height_unit, weight_value, weight_unit, dietary_goal }) {
  const hCm = height_unit === 'in' ? Number(height_value) * 2.54 : Number(height_value)
  const wKg = weight_unit === 'lb' ? Number(weight_value) * 0.45359237 : Number(weight_value)
  if (!hCm || !wKg) return null
  const baseline = 22.0 * wKg + 6.0 * hCm
  const mult =
    dietary_goal === 'weight_loss'
      ? 0.8
      : dietary_goal === 'weight_gain'
        ? 1.15
        : 1.0 // maintain/eat_healthy
  const raw = baseline * mult
  const rounded = Math.round(raw / 10) * 10
  return Math.max(1200, Math.min(4000, rounded))
}

function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [formData, setFormData] = useState({
    username: '',
    role: 'user',
    dietary_goal: 'maintain',
    height_value: '',
    height_unit: 'cm',
    weight_value: '',
    weight_unit: 'kg',
  })

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    // #region agent log
    try {
      fetch('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: 'Users.jsx:loadUsers',
          message: 'Starting loadUsers',
          data: {},
          timestamp: Date.now(),
          sessionId: 'debug-session',
          runId: 'run1',
          hypothesisId: 'C'
        })
      }).catch(() => {});
    } catch {}
    // #endregion
    try {
      setLoading(true)
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'Users.jsx:loadUsers',
            message: 'Calling usersAPI.getAll',
            data: {},
            timestamp: Date.now(),
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'C'
          })
        }).catch(() => {});
      } catch {}
      // #endregion
      const response = await usersAPI.getAll()
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'Users.jsx:loadUsers',
            message: 'API call successful',
            data: { status: response.status, dataLength: response.data?.length },
            timestamp: Date.now(),
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'C'
          })
        }).catch(() => {});
      } catch {}
      // #endregion
      setUsers(response.data)
    } catch (error) {
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'Users.jsx:loadUsers',
            message: 'Error in loadUsers',
            data: {
              error: error.message,
              errorStack: error.stack,
              responseStatus: error.response?.status,
              responseData: error.response?.data
            },
            timestamp: Date.now(),
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'C'
          })
        }).catch(() => {});
      } catch {}
      // #endregion
      console.error('Error loading users:', error)
      const errorMsg = error.response?.data?.error || error.message || 'Failed to load users'
      alert(`Failed to load users: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        height_value: Number(formData.height_value),
        weight_value: Number(formData.weight_value),
      }
      try {
        if (editingUser) {
          await usersAPI.update(editingUser.user_id, payload)
        } else {
          await usersAPI.create(payload)
        }
      } catch (err) {
        if (err?.response?.data?.requires_confirmation) {
          const ok = window.confirm(
            `${err.response.data.error}\n\nPreview target calories: ${err.response.data.preview_target_calories}\n\nContinue?`,
          )
          if (!ok) return
          const payload2 = { ...payload, confirm_unrealistic: true }
          if (editingUser) {
            await usersAPI.update(editingUser.user_id, payload2)
          } else {
            await usersAPI.create(payload2)
          }
        } else {
          throw err
        }
      }
      setShowModal(false)
      setEditingUser(null)
      setFormData({
        username: '',
        role: 'user',
        dietary_goal: 'maintain',
        height_value: '',
        height_unit: 'cm',
        weight_value: '',
        weight_unit: 'kg',
      })
      loadUsers()
    } catch (error) {
      console.error('Error saving user:', error)
      alert(error.response?.data?.error || 'Failed to save user')
    }
  }

  const handleEdit = (user) => {
    setEditingUser(user)
    setFormData({
      username: user.username,
      role: user.role || 'user',
      dietary_goal: user.dietary_goal || 'maintain',
      height_value: user.height_value ?? '',
      height_unit: user.height_unit || 'cm',
      weight_value: user.weight_value ?? '',
      weight_unit: user.weight_unit || 'kg',
    })
    setShowModal(true)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this user? All consumption data will be deleted.')) {
      return
    }
    try {
      await usersAPI.delete(id)
      loadUsers()
    } catch (error) {
      console.error('Error deleting user:', error)
      alert(error.response?.data?.error || 'Failed to delete user')
    }
  }

  const openCreateModal = () => {
    setEditingUser(null)
    setFormData({
      username: '',
      role: 'user',
      dietary_goal: 'maintain',
      height_value: '',
      height_unit: 'cm',
      weight_value: '',
      weight_unit: 'kg',
    })
    setShowModal(true)
  }

  if (loading) {
    return <div className="card">Loading users...</div>
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2>User Management</h2>
          <button className="btn btn-primary" onClick={openCreateModal}>
            + Create User
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Role</th>
                <th>Dietary Goal</th>
                <th>Height</th>
                <th>Weight</th>
                <th>Target Calories</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem' }}>
                    No users found. Create your first user!
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.user_id}>
                    <td>{user.user_id}</td>
                    <td>{user.username}</td>
                    <td>{user.role}</td>
                    <td>{user.dietary_goal}</td>
                    <td>
                      {user.height_value ? `${Number(user.height_value).toFixed(1)} ${user.height_unit}` : '—'}
                    </td>
                    <td>
                      {user.weight_value ? `${Number(user.weight_value).toFixed(1)} ${user.weight_unit}` : '—'}
                    </td>
                    <td>{user.target_calories ? `${user.target_calories} kcal` : '—'}</td>
                    <td>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ marginRight: '0.5rem', padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                        onClick={() => handleEdit(user)}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                        onClick={() => handleDelete(user.user_id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="modal" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingUser ? 'Edit User' : 'Create User'}</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                  disabled={!!editingUser}
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })}>
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>Dietary Goal</label>
                <select
                  value={formData.dietary_goal}
                  onChange={(e) => setFormData({ ...formData, dietary_goal: e.target.value })}
                >
                  {GOALS.map((g) => (
                    <option key={g.value} value={g.value}>
                      {g.label}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Height *</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.height_value}
                    onChange={(e) => setFormData({ ...formData, height_value: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Height unit</label>
                  <select
                    value={formData.height_unit}
                    onChange={(e) => setFormData({ ...formData, height_unit: e.target.value })}
                  >
                    <option value="cm">cm</option>
                    <option value="in">in</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Weight *</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.weight_value}
                    onChange={(e) => setFormData({ ...formData, weight_value: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Weight unit</label>
                  <select
                    value={formData.weight_unit}
                    onChange={(e) => setFormData({ ...formData, weight_unit: e.target.value })}
                  >
                    <option value="kg">kg</option>
                    <option value="lb">lb</option>
                  </select>
                </div>
              </div>

              <div className="stat-card" style={{ marginBottom: '1rem' }}>
                <h3>Target calories (auto-calculated)</h3>
                <div className="value">{calcTargetLocal(formData) ?? '—'}</div>
                <div style={{ color: '#666', marginTop: '0.5rem' }}>
                  Auto-calculated based on goal, height and weight.
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingUser ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Users

