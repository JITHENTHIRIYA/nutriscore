import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  signup: (data) => api.post('/auth/signup', data),
}

export const profileAPI = {
  get: () => api.get('/profile'),
  preview: (data) => api.post('/profile/preview', data),
  update: (data) => api.put('/profile', data),
  complete: (data) => api.post('/profile/complete', data),
}

// Users API
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
}

// Foods API
export const foodsAPI = {
  getAll: (params) => api.get('/foods', { params }),
  getById: (id) => api.get(`/foods/${id}`),
  create: (data) => api.post('/foods', data),
  update: (id, data) => api.put(`/foods/${id}`, data),
  delete: (id) => api.delete(`/foods/${id}`),
}

// Consumption API
export const consumptionAPI = {
  getAll: (params) => api.get('/consumption', { params }),
  getById: (id) => api.get(`/consumption/${id}`),
  create: (data) => api.post('/consumption', data),
  update: (id, data) => api.put(`/consumption/${id}`, data),
  delete: (id) => api.delete(`/consumption/${id}`),
}

// Analytics API
export const analyticsAPI = {
  getFoodNutrition: (params) => api.get('/analytics/food-nutrition', { params }),
  getTopFoods: (params) => api.get('/analytics/top-foods', { params }),
  getUserProgress: (userId, params) => api.get(`/analytics/user-progress/${userId}`, { params }),
  getDailyHealthScore: (userId, params) => api.get(`/analytics/daily-health-score/${userId}`, { params }),
  getOverallHealthScore: (userId) => api.get(`/analytics/overall-health-score/${userId}`),
  getMealDistribution: (params) => api.get('/analytics/meal-distribution', { params }),
  getPopularFoods: (params) => api.get('/analytics/popular-foods', { params }),
}

// Health check
export const healthCheck = () => api.get('/health')

export default api

