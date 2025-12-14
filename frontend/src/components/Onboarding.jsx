import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { profileAPI } from '../api'
import { useAuth } from '../auth/AuthContext'

const GOALS = [
  { value: 'weight_loss', label: 'Weight loss (20% deficit)' },
  { value: 'maintain', label: 'Maintain current weight' },
  { value: 'eat_healthy', label: 'Eat healthy' },
  { value: 'weight_gain', label: 'Weight gain (15% surplus)' },
]

function Onboarding() {
  const { user, refresh } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    height_value: '',
    height_unit: 'cm',
    weight_value: '',
    weight_unit: 'kg',
    dietary_goal: 'maintain',
    confirm_unrealistic: false,
  })
  const [preview, setPreview] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [requiresConfirmation, setRequiresConfirmation] = useState(false)

  // If user already has complete profile, redirect to dashboard
  useEffect(() => {
    if (user?.profile_complete) {
      navigate('/dashboard')
    }
  }, [user, navigate])

  // Live preview of target calories
  useEffect(() => {
    const h = form.height_value
    const w = form.weight_value
    if (h === '' || w === '' || isNaN(Number(h)) || isNaN(Number(w))) {
      setPreview(null)
      return
    }
    profileAPI
      .preview({
        height_value: Number(h),
        height_unit: form.height_unit,
        weight_value: Number(w),
        weight_unit: form.weight_unit,
        dietary_goal: form.dietary_goal,
      })
      .then((res) => {
        setPreview(res.data)
        setRequiresConfirmation(res.data.requires_confirmation || false)
      })
      .catch(() => {
        setPreview(null)
        setRequiresConfirmation(false)
      })
  }, [form.height_value, form.height_unit, form.weight_value, form.weight_unit, form.dietary_goal])

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Validation
    if (!form.height_value || !form.weight_value) {
      setError('Please enter both height and weight')
      return
    }

    if (isNaN(Number(form.height_value)) || isNaN(Number(form.weight_value))) {
      setError('Height and weight must be valid numbers')
      return
    }

    // If requires confirmation and user hasn't confirmed, show error
    if (requiresConfirmation && !form.confirm_unrealistic) {
      setError('Please confirm your height/weight values if they look unusual')
      return
    }

    setSaving(true)
    try {
      const payload = {
        height_value: Number(form.height_value),
        height_unit: form.height_unit,
        weight_value: Number(form.weight_value),
        weight_unit: form.weight_unit,
        dietary_goal: form.dietary_goal,
      }
      if (requiresConfirmation) {
        payload.confirm_unrealistic = true
      }

      const res = await profileAPI.complete(payload)
      // Refresh auth context to update profile_complete flag
      await refresh()
      // Redirect to dashboard
      navigate('/dashboard')
    } catch (e) {
      if (e?.response?.data?.requires_confirmation) {
        setRequiresConfirmation(true)
        setPreview({
          preview_target_calories: e.response.data.preview_target_calories,
          requires_confirmation: true,
        })
        setError(e.response.data.error)
      } else {
        setError(e?.response?.data?.error || 'Failed to complete profile')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card" style={{ maxWidth: 600, margin: '2rem auto' }}>
      <div className="card-header">
        <h2>Welcome! Let's set up your profile</h2>
        <p style={{ color: '#666', marginTop: '0.5rem', fontSize: '0.9rem' }}>
          We need a few details to calculate your personalized calorie target.
        </p>
      </div>
      <form onSubmit={onSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px', gap: '1rem', marginBottom: '1rem' }}>
          <div className="form-group">
            <label>Height *</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={form.height_value}
              onChange={(e) => setForm({ ...form, height_value: e.target.value })}
              placeholder="Enter height"
              required
            />
          </div>
          <div className="form-group">
            <label>Unit</label>
            <select
              value={form.height_unit}
              onChange={(e) => setForm({ ...form, height_unit: e.target.value })}
            >
              <option value="cm">cm</option>
              <option value="in">in</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px', gap: '1rem', marginBottom: '1rem' }}>
          <div className="form-group">
            <label>Weight *</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={form.weight_value}
              onChange={(e) => setForm({ ...form, weight_value: e.target.value })}
              placeholder="Enter weight"
              required
            />
          </div>
          <div className="form-group">
            <label>Unit</label>
            <select
              value={form.weight_unit}
              onChange={(e) => setForm({ ...form, weight_unit: e.target.value })}
            >
              <option value="kg">kg</option>
              <option value="lb">lb</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Dietary Goal *</label>
          <select
            value={form.dietary_goal}
            onChange={(e) => setForm({ ...form, dietary_goal: e.target.value })}
            required
          >
            {GOALS.map((g) => (
              <option key={g.value} value={g.value}>
                {g.label}
              </option>
            ))}
          </select>
        </div>

        {preview && (
          <div
            style={{
              padding: '1rem',
              backgroundColor: '#f0f7ff',
              borderRadius: '4px',
              marginBottom: '1rem',
            }}
          >
            <strong>Your target calories: {preview.preview_target_calories} kcal/day</strong>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: '#666' }}>
              Auto-calculated based on your goal, height and weight.
            </p>
          </div>
        )}

        {requiresConfirmation && (
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={form.confirm_unrealistic || false}
                onChange={(e) => setForm({ ...form, confirm_unrealistic: e.target.checked })}
              />
              <span>I confirm my height and weight values are correct</span>
            </label>
          </div>
        )}

        {error && <div style={{ color: '#dc3545', marginBottom: '1rem' }}>{error}</div>}

        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={saving || !form.height_value || !form.weight_value}>
            {saving ? 'Saving…' : 'Complete Setup'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default Onboarding

