import React, { useEffect, useState } from 'react'
import { profileAPI } from '../api'
import { useAuth } from '../auth/AuthContext'

const GOALS = [
  { value: 'weight_loss', label: 'Weight loss (20% deficit)' },
  { value: 'maintain', label: 'Maintain' },
  { value: 'eat_healthy', label: 'Eat healthy' },
  { value: 'weight_gain', label: 'Weight gain (15% surplus)' },
]

function Profile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({
    height_value: '',
    height_unit: 'cm',
    weight_value: '',
    weight_unit: 'kg',
    dietary_goal: 'maintain',
  })
  const [preview, setPreview] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    const res = await profileAPI.get()
    setProfile(res.data)
    setForm({
      height_value: res.data.height_value ?? '',
      height_unit: res.data.height_unit ?? 'cm',
      weight_value: res.data.weight_value ?? '',
      weight_unit: res.data.weight_unit ?? 'kg',
      dietary_goal: res.data.dietary_goal ?? 'maintain',
    })
  }

  useEffect(() => {
    load().catch((e) => setError(e?.response?.data?.error || 'Failed to load profile'))
  }, [])

  useEffect(() => {
    const h = form.height_value
    const w = form.weight_value
    if (h === '' || w === '') {
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
      .then((res) => setPreview(res.data))
      .catch(() => setPreview(null))
  }, [form.height_value, form.height_unit, form.weight_value, form.weight_unit, form.dietary_goal])

  const onSave = async () => {
    setError('')
    setSaving(true)
    try {
      const payload = {
        height_value: Number(form.height_value),
        height_unit: form.height_unit,
        weight_value: Number(form.weight_value),
        weight_unit: form.weight_unit,
        dietary_goal: form.dietary_goal,
      }
      try {
        const res = await profileAPI.update(payload)
        setProfile(res.data)
      } catch (e) {
        if (e?.response?.data?.requires_confirmation) {
          const ok = window.confirm(
            `${e.response.data.error}\n\nPreview target calories: ${e.response.data.preview_target_calories}\n\nContinue?`,
          )
          if (!ok) return
          const res2 = await profileAPI.update({ ...payload, confirm_unrealistic: true })
          setProfile(res2.data)
        } else {
          throw e
        }
      }
      await load()
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>Profile</h2>
        <div style={{ color: '#666' }}>
          Signed in as <b>{user?.username}</b> ({user?.role})
        </div>
      </div>

      {error && <div style={{ color: '#dc3545', marginBottom: '1rem' }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div className="form-group">
          <label>Height</label>
          <input
            type="number"
            step="0.1"
            value={form.height_value}
            onChange={(e) => setForm({ ...form, height_value: e.target.value })}
            placeholder="e.g. 170"
          />
        </div>
        <div className="form-group">
          <label>Height unit</label>
          <select value={form.height_unit} onChange={(e) => setForm({ ...form, height_unit: e.target.value })}>
            <option value="cm">cm</option>
            <option value="in">in</option>
          </select>
        </div>
        <div className="form-group">
          <label>Weight</label>
          <input
            type="number"
            step="0.1"
            value={form.weight_value}
            onChange={(e) => setForm({ ...form, weight_value: e.target.value })}
            placeholder="e.g. 70"
          />
        </div>
        <div className="form-group">
          <label>Weight unit</label>
          <select value={form.weight_unit} onChange={(e) => setForm({ ...form, weight_unit: e.target.value })}>
            <option value="kg">kg</option>
            <option value="lb">lb</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label>Dietary goal</label>
        <select value={form.dietary_goal} onChange={(e) => setForm({ ...form, dietary_goal: e.target.value })}>
          {GOALS.map((g) => (
            <option key={g.value} value={g.value}>
              {g.label}
            </option>
          ))}
        </select>
      </div>

      <div className="stat-card" style={{ marginBottom: '1rem' }}>
        <h3>Target calories (auto-calculated)</h3>
        <div className="value">
          {preview?.preview_target_calories ?? profile?.target_calories ?? '—'}
        </div>
        <div style={{ color: '#666', marginTop: '0.5rem' }}>
          Auto-calculated based on your goal, height and weight.
        </div>
      </div>

      <div className="form-actions">
        <button className="btn btn-primary" onClick={onSave} disabled={saving}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  )
}

export default Profile


