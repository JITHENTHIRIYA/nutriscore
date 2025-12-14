import React, { useState, useEffect } from 'react'
import { consumptionAPI, foodsAPI } from '../api'
import { useAuth } from '../auth/AuthContext'

const MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner', 'Snack']

function Consumption() {
  const { user } = useAuth()
  const [consumption, setConsumption] = useState([])
  const [foods, setFoods] = useState([])
  const [filteredFoods, setFilteredFoods] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchingFoods, setSearchingFoods] = useState(false)
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [showModal, setShowModal] = useState(false)
  const [editingEntry, setEditingEntry] = useState(null)
  const [foodSearch, setFoodSearch] = useState('')
  const [debouncedFoodSearch, setDebouncedFoodSearch] = useState('')
  const [showFoodDropdown, setShowFoodDropdown] = useState(false)
  const [formData, setFormData] = useState({
    food_id: '',
    date: new Date().toISOString().split('T')[0],
    portion_size: 1.0,
    meal_type: '',
  })

  useEffect(() => {
    loadFoods()
  }, [])

  useEffect(() => {
    if (user?.user_id) loadConsumption()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.user_id, selectedDate])

  // Debounce food search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFoodSearch(foodSearch)
    }, 300) // Wait 300ms after user stops typing

    return () => clearTimeout(timer)
  }, [foodSearch])

  // Search foods via API when user types, or show initial foods when no search
  useEffect(() => {
    const searchFoods = async () => {
      if (!debouncedFoodSearch.trim()) {
        // No search: show first 50 from preloaded foods
        setFilteredFoods(foods.slice(0, 50))
        return
      }

      // User is searching: query API to find all matching foods
      setSearchingFoods(true)
      try {
        const response = await foodsAPI.getAll({ 
          search: debouncedFoodSearch,
          limit: 50 // Get up to 50 results from API
        })
        setFilteredFoods(response.data)
      } catch (error) {
        console.error('Error searching foods:', error)
        // Fallback to local filtering if API fails
        const searchLower = debouncedFoodSearch.toLowerCase()
        const filtered = foods
          .filter((food) => 
            food.food_name.toLowerCase().includes(searchLower) ||
            food.food_id.toString().includes(searchLower)
          )
          .slice(0, 20)
        setFilteredFoods(filtered)
      } finally {
        setSearchingFoods(false)
      }
    }

    searchFoods()
  }, [debouncedFoodSearch, foods])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showFoodDropdown && !event.target.closest('.food-search-container')) {
        setShowFoodDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showFoodDropdown])

  const loadFoods = async () => {
    try {
      // Load initial foods for dropdown (first 1000, ordered by name)
      // When user searches, we'll query API directly to find all matches
      const response = await foodsAPI.getAll({ limit: 1000 })
      setFoods(response.data)
      // Set initial filtered foods (first 50)
      setFilteredFoods(response.data.slice(0, 50))
    } catch (error) {
      console.error('Error loading foods:', error)
    }
  }

  const loadConsumption = async () => {
    try {
      setLoading(true)
      const params = {}
      if (selectedDate) params.date = selectedDate
      const response = await consumptionAPI.getAll(params)
      setConsumption(response.data)
    } catch (error) {
      console.error('Error loading consumption:', error)
      alert('Failed to load consumption data')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.food_id) {
      alert('Please select a food item')
      return
    }
    try {
      const data = {
        ...formData,
        food_id: parseInt(formData.food_id),
        portion_size: parseFloat(formData.portion_size),
      }
      if (editingEntry) {
        await consumptionAPI.update(editingEntry.entry_id, data)
      } else {
        await consumptionAPI.create(data)
      }
      setShowModal(false)
      setShowFoodDropdown(false)
      setEditingEntry(null)
      resetForm()
      loadConsumption()
    } catch (error) {
      console.error('Error saving consumption:', error)
      alert(error.response?.data?.error || 'Failed to save consumption entry')
    }
  }

  const handleEdit = (entry) => {
    setEditingEntry(entry)
    const selectedFood = foods.find(f => f.food_id === entry.food_id)
    setFormData({
      food_id: entry.food_id.toString(),
      date: entry.date,
      portion_size: parseFloat(entry.portion_size).toFixed(2),
      meal_type: entry.meal_type || '',
    })
    setFoodSearch(selectedFood ? `[${selectedFood.food_id}] ${selectedFood.food_name}` : '')
    setShowModal(true)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this consumption entry?')) {
      return
    }
    try {
      await consumptionAPI.delete(id)
      loadConsumption()
    } catch (error) {
      console.error('Error deleting consumption:', error)
      alert(error.response?.data?.error || 'Failed to delete entry')
    }
  }

  const resetForm = () => {
    setFormData({
      food_id: '',
      date: selectedDate,
      portion_size: 1.0,
      meal_type: '',
    })
    setFoodSearch('')
    setShowFoodDropdown(false)
  }

  const openCreateModal = () => {
    setEditingEntry(null)
    setFormData({
      food_id: '',
      date: selectedDate,
      portion_size: 1.0,
      meal_type: '',
    })
    setFoodSearch('')
    setShowFoodDropdown(false)
    setShowModal(true)
  }

  const handleFoodSelect = (food) => {
    setFormData({ ...formData, food_id: food.food_id.toString() })
    setFoodSearch(`[${food.food_id}] ${food.food_name}`)
    setShowFoodDropdown(false)
  }

  const getTotalNutrition = () => {
    return consumption.reduce(
      (acc, entry) => ({
        calories: acc.calories + parseFloat(entry.calories),
        protein: acc.protein + parseFloat(entry.protein),
        carbs: acc.carbs + parseFloat(entry.carbs),
        fat: acc.fat + parseFloat(entry.fat),
        fiber: acc.fiber + parseFloat(entry.fiber || 0),
        health_score: acc.health_score + parseFloat(entry.health_score || 0),
      }),
      { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, health_score: 0 }
    )
  }

  const totals = getTotalNutrition()
  const avgHealthScore = consumption.length > 0 ? totals.health_score / consumption.length : 0

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2>Log Food Consumption</h2>
          <button className="btn btn-primary" onClick={openCreateModal} disabled={!user?.user_id}>
            + Log Food
          </button>
        </div>

        <div className="search-bar">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </div>

        {consumption.length > 0 && (
          <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="stat-card">
              <h3>Total Calories</h3>
              <div className="value">{totals.calories.toFixed(1)}</div>
            </div>
            <div className="stat-card">
              <h3>Total Protein</h3>
              <div className="value">{totals.protein.toFixed(1)}g</div>
            </div>
            <div className="stat-card">
              <h3>Total Carbs</h3>
              <div className="value">{totals.carbs.toFixed(1)}g</div>
            </div>
            <div className="stat-card">
              <h3>Total Fat</h3>
              <div className="value">{totals.fat.toFixed(1)}g</div>
            </div>
            <div className="stat-card">
              <h3>Total Fiber</h3>
              <div className="value">{totals.fiber.toFixed(1)}g</div>
            </div>
            <div className="stat-card">
              <h3>Avg Health Score</h3>
              <div className="value">{avgHealthScore.toFixed(0)}</div>
            </div>
          </div>
        )}

        {loading ? (
          <div>Loading consumption data...</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Food ID</th>
                  <th>Food</th>
                  <th>Portion</th>
                  <th>Calories</th>
                  <th>Protein</th>
                  <th>Carbs</th>
                  <th>Fat</th>
                  <th>Fiber</th>
                  <th>Health Score</th>
                  <th>Meal</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {consumption.length === 0 ? (
                  <tr>
                    <td colSpan="11" style={{ textAlign: 'center', padding: '2rem' }}>
                      {`No consumption entries for this date. Log your first meal!`}
                    </td>
                  </tr>
                ) : (
                  consumption.map((entry) => (
                    <tr key={entry.entry_id}>
                      <td>{entry.food_id}</td>
                      <td>{entry.food_name}</td>
                      <td>{parseFloat(entry.portion_size).toFixed(2)}x</td>
                      <td>{parseFloat(entry.calories).toFixed(1)}</td>
                      <td>{parseFloat(entry.protein).toFixed(1)}g</td>
                      <td>{parseFloat(entry.carbs).toFixed(1)}g</td>
                      <td>{parseFloat(entry.fat).toFixed(1)}g</td>
                      <td>{parseFloat(entry.fiber || 0).toFixed(1)}g</td>
                      <td>{entry.health_score || 'N/A'}</td>
                      <td>{entry.meal_type || '-'}</td>
                      <td>
                        <button
                          className="btn btn-secondary"
                          style={{ marginRight: '0.5rem', padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                          onClick={() => handleEdit(entry)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger"
                          style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                          onClick={() => handleDelete(entry.entry_id)}
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
        )}
      </div>

      {showModal && (
        <div 
          className="modal" 
          onClick={() => {
            setShowModal(false)
            setShowFoodDropdown(false)
          }}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingEntry ? 'Edit Consumption Entry' : 'Log Food Consumption'}</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group food-search-container" style={{ position: 'relative' }}>
                <label>Food *</label>
                <input
                  type="text"
                  placeholder="Search for food by name or ID..."
                  value={foodSearch}
                  onChange={(e) => {
                    setFoodSearch(e.target.value)
                    setShowFoodDropdown(true)
                    if (!e.target.value) {
                      setFormData({ ...formData, food_id: '' })
                    }
                  }}
                  onFocus={() => setShowFoodDropdown(true)}
                  required={!formData.food_id}
                  style={{ width: '100%' }}
                />
                {showFoodDropdown && (
                  <div
                    className="food-search-container"
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      backgroundColor: 'white',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      zIndex: 1000,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      marginTop: '4px',
                    }}
                  >
                    {searchingFoods ? (
                      <div style={{ padding: '1rem', textAlign: 'center', color: '#666' }}>
                        Searching...
                      </div>
                    ) : filteredFoods.length > 0 ? (
                      filteredFoods.map((food) => (
                        <div
                          key={food.food_id}
                          onClick={() => handleFoodSelect(food)}
                          style={{
                            padding: '0.75rem',
                            cursor: 'pointer',
                            borderBottom: '1px solid #eee',
                            backgroundColor: formData.food_id === food.food_id.toString() ? '#f0f7ff' : 'white',
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f5f5f5')}
                          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = formData.food_id === food.food_id.toString() ? '#f0f7ff' : 'white')}
                        >
                          <strong>[{food.food_id}]</strong> {food.food_name}
                          <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.25rem' }}>
                            {parseFloat(food.calories).toFixed(0)} cal • {parseFloat(food.protein).toFixed(1)}g protein
                          </div>
                        </div>
                      ))
                    ) : (
                      <div style={{ padding: '1rem', textAlign: 'center', color: '#666' }}>
                        {foodSearch ? 'No foods found. Try a different search term.' : 'Start typing to search for foods...'}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="form-group">
                <label>Date *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Portion Size (multiplier) *</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={formData.portion_size}
                  onChange={(e) => setFormData({ ...formData, portion_size: parseFloat(e.target.value) || 1.0 })}
                  required
                />
                <small style={{ color: '#666', fontSize: '0.9rem' }}>
                  Enter 1.0 for standard serving, 2.0 for double serving, etc.
                </small>
              </div>
              <div className="form-group">
                <label>Meal Type</label>
                <select
                  value={formData.meal_type}
                  onChange={(e) => setFormData({ ...formData, meal_type: e.target.value })}
                >
                  <option value="">Not specified</option>
                  {MEAL_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingEntry ? 'Update' : 'Log Food'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Consumption

