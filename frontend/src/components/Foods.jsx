import React, { useState, useEffect } from 'react'
import { foodsAPI } from '../api'
import { useAuth } from '../auth/AuthContext'

function Foods() {
  const { user } = useAuth()
  const [foods, setFoods] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingFood, setEditingFood] = useState(null)
  const [formData, setFormData] = useState({
    food_name: '',
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0,
    fiber: 0,
    sugars: 0,
    nutrition_density: 0,
  })

  // Debounce search input to avoid reloading on every keystroke
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
    }, 300) // Wait 300ms after user stops typing

    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    loadFoods()
  }, [debouncedSearch])

  const loadFoods = async () => {
    try {
      setLoading(true)
      const params = {}
      if (debouncedSearch) params.search = debouncedSearch
      const response = await foodsAPI.getAll(params)
      setFoods(response.data)
    } catch (error) {
      console.error('Error loading foods:', error)
      alert('Failed to load foods')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingFood) {
        await foodsAPI.update(editingFood.food_id, formData)
      } else {
        await foodsAPI.create(formData)
      }
      setShowModal(false)
      setEditingFood(null)
      resetForm()
      loadFoods()
    } catch (error) {
      console.error('Error saving food:', error)
      alert(error.response?.data?.error || 'Failed to save food')
    }
  }

  const handleEdit = (food) => {
    setEditingFood(food)
    setFormData({
      food_name: food.food_name,
      calories: food.calories,
      protein: food.protein,
      carbs: food.carbs,
      fat: food.fat,
      fiber: food.fiber,
      sugars: food.sugars,
      nutrition_density: food.nutrition_density || 0,
    })
    setShowModal(true)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this food item?')) {
      return
    }
    try {
      await foodsAPI.delete(id)
      loadFoods()
    } catch (error) {
      console.error('Error deleting food:', error)
      alert(error.response?.data?.error || 'Failed to delete food. It may be referenced in consumption records.')
    }
  }

  const resetForm = () => {
    setFormData({
      food_name: '',
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0,
      fiber: 0,
      sugars: 0,
      nutrition_density: 0,
    })
  }

  const openCreateModal = () => {
    setEditingFood(null)
    resetForm()
    setShowModal(true)
  }

  if (loading) {
    return <div className="card">Loading foods...</div>
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2>Food Catalog</h2>
          {user?.user_id && (
            <button className="btn btn-primary" onClick={openCreateModal}>
              + Add Food
            </button>
          )}
        </div>

        <div className="search-bar">
          <input
            type="text"
            placeholder="Search foods..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Calories</th>
                <th>Protein</th>
                <th>Carbs</th>
                <th>Fat</th>
                <th>Fiber</th>
                <th>Sugars</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {foods.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem' }}>
                    No foods found. {search ? 'Try adjusting your search.' : 'Add your first food!'}
                  </td>
                </tr>
              ) : (
                foods.map((food) => (
                  <tr key={food.food_id}>
                    <td>{food.food_id}</td>
                    <td>{food.food_name}</td>
                    <td>{parseFloat(food.calories).toFixed(1)}</td>
                    <td>{parseFloat(food.protein).toFixed(1)}g</td>
                    <td>{parseFloat(food.carbs).toFixed(1)}g</td>
                    <td>{parseFloat(food.fat).toFixed(1)}g</td>
                    <td>{parseFloat(food.fiber).toFixed(1)}g</td>
                    <td>{parseFloat(food.sugars).toFixed(1)}g</td>
                    <td>
                      {(user?.role === 'admin' || (food.created_by_user_id != null && food.created_by_user_id === user?.user_id)) ? (
                        <>
                          <button
                            className="btn btn-secondary"
                            style={{ marginRight: '0.5rem', padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                            onClick={() => handleEdit(food)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                            onClick={() => handleDelete(food.food_id)}
                          >
                            Delete
                          </button>
                        </>
                      ) : (
                        <span style={{ color: '#666' }}>Read-only</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {user?.user_id && showModal && (
        <div className="modal" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingFood ? 'Edit Food' : 'Add Food'}</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Food Name *</label>
                <input
                  type="text"
                  value={formData.food_name}
                  onChange={(e) => setFormData({ ...formData, food_name: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Calories *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.calories}
                    onChange={(e) => setFormData({ ...formData, calories: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Protein (g) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.protein}
                    onChange={(e) => setFormData({ ...formData, protein: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Carbs (g) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.carbs}
                    onChange={(e) => setFormData({ ...formData, carbs: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Fat (g) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.fat}
                    onChange={(e) => setFormData({ ...formData, fat: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Fiber (g) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.fiber}
                    onChange={(e) => setFormData({ ...formData, fiber: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Sugars (g) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.sugars}
                    onChange={(e) => setFormData({ ...formData, sugars: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Nutrition Density</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.nutrition_density}
                  onChange={(e) => setFormData({ ...formData, nutrition_density: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingFood ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Foods

