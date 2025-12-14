import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { analyticsAPI, usersAPI } from '../api'
import { useAuth } from '../auth/AuthContext'

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a', '#fee140', '#30cfd0']

function Dashboard() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [selectedUserId, setSelectedUserId] = useState('')
  const [userProgress, setUserProgress] = useState([])
  const [overallHealth, setOverallHealth] = useState(null)
  const [mealDistribution, setMealDistribution] = useState([])
  const [popularFoods, setPopularFoods] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user?.role === 'admin') {
      loadUsers()
    } else if (user?.user_id) {
      setSelectedUserId(String(user.user_id))
    }
    loadPopularFoods()
  }, [user])

  useEffect(() => {
    if (selectedUserId) {
      loadUserProgress()
      loadOverallHealthScore()
      loadMealDistribution()
      // For admins, popular foods can be user-scoped; for normal users backend uses session user anyway.
      loadPopularFoods()
    }
  }, [selectedUserId])

  const loadUsers = async () => {
    try {
      const response = await usersAPI.getAll()
      setUsers(response.data)
      if (response.data.length > 0) {
        setSelectedUserId(response.data[0].user_id.toString())
      }
    } catch (error) {
      console.error('Error loading users:', error)
    }
  }

  const loadUserProgress = async () => {
    if (!selectedUserId) return
    try {
      setLoading(true)
      const response = await analyticsAPI.getUserProgress(selectedUserId, { days: 30 })
      setUserProgress(response.data)
    } catch (error) {
      console.error('Error loading user progress:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadOverallHealthScore = async () => {
    if (!selectedUserId) return
    try {
      const response = await analyticsAPI.getOverallHealthScore(selectedUserId)
      setOverallHealth(response.data)
    } catch (error) {
      console.error('Error loading overall health score:', error)
      setOverallHealth(null)
    }
  }

  const loadMealDistribution = async () => {
    if (!selectedUserId) return
    try {
      const response = await analyticsAPI.getMealDistribution({ user_id: selectedUserId, days: 30 })
      // Transform data to use 'name' instead of 'meal_type' for the pie chart
      const transformedData = response.data.map(item => ({
        name: item.meal_type || 'Unknown',
        count: item.count,
        total_calories: item.total_calories,
        avg_health_score: item.avg_health_score
      }))
      setMealDistribution(transformedData)
    } catch (error) {
      console.error('Error loading meal distribution:', error)
    }
  }

  const loadPopularFoods = async () => {
    try {
      const params = user?.role === 'admin' && selectedUserId ? { user_id: selectedUserId, limit: 10 } : { limit: 10 }
      const response = await analyticsAPI.getPopularFoods(params)
      setPopularFoods(response.data)
    } catch (error) {
      console.error('Error loading popular foods:', error)
    }
  }

  return (
    <div>
      {user?.role === 'admin' && users.length > 0 && (
        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
          <select
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '2px solid #e0e0e0' }}
          >
            {users.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.username}
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedUserId && (
        <>
          {/* Overall health score */}
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Overall Health Score</h3>
              <div className="value">
                {overallHealth?.overall_health_score != null ? Number(overallHealth.overall_health_score).toFixed(2) : '—'}
              </div>
            </div>
            <div className="stat-card">
              <h3>Days Tracked</h3>
              <div className="value">{overallHealth?.days_tracked ?? '—'}</div>
            </div>
            <div className="stat-card">
              <h3>Total Entries</h3>
              <div className="value">{overallHealth?.entries_count ?? '—'}</div>
            </div>
          </div>

          {/* Chart 3: User Progress Over Time (Line Chart) */}
          <div className="chart-container">
            <h3>User Progress Over Time (Last 30 Days)</h3>
            {loading ? (
              <div>Loading progress data...</div>
            ) : userProgress.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No progress data available. Start logging your meals!
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={userProgress}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="total_calories"
                    stroke="#667eea"
                    name="Total Calories"
                    strokeWidth={2}
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="target_calories"
                    stroke="#dc3545"
                    name="Target Calories"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="avg_health_score"
                    stroke="#28a745"
                    name="Daily Health Score"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Chart 4: Meal Type Distribution (Pie Chart) */}
          <div className="chart-container">
            <h3>Meal Type Distribution (Last 30 Days)</h3>
            {mealDistribution.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No meal distribution data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={mealDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {mealDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}

      {/* Chart 5: Most Consumed Foods */}
      <div className="chart-container">
        <h3>Most Consumed Foods</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Food ID</th>
                <th>Food Name</th>
                <th>Times Consumed</th>
                <th>Avg Health Score</th>
                <th>Total Calories</th>
              </tr>
            </thead>
            <tbody>
              {popularFoods.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                    No consumption data available.
                  </td>
                </tr>
              ) : (
                popularFoods.map((food) => (
                  <tr key={food.food_id}>
                    <td>{food.food_id}</td>
                    <td>{food.food_name}</td>
                    <td>{food.times_consumed || 0}</td>
                    <td>{food.avg_health_score || 'N/A'}</td>
                    <td>{parseFloat(food.total_calories_consumed || 0).toFixed(1)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

