import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

export const auditApi = {
  uploadTask: (formData) => api.post('/audit/upload', formData),

  getTasks: (params) => api.get('/audit/tasks', { params }),

  getTask: (taskId) => api.get(`/audit/tasks/${taskId}`),

  getTaskDetail: (taskId) => api.get(`/audit/tasks/${taskId}/detail`),

  deleteTask: (taskId) => api.delete(`/audit/tasks/${taskId}`),

  getStatistics: () => api.get('/audit/statistics')
}

export const rulesApi = {
  getRules: (params) => api.get('/rules', { params }),

  getRule: (ruleId) => api.get(`/rules/${ruleId}`),

  createRule: (data) => api.post('/rules', data),

  updateRule: (ruleId, data) => api.put(`/rules/${ruleId}`, data),

  deleteRule: (ruleId) => api.delete(`/rules/${ruleId}`),

  importRules: (yaml) => api.post('/rules/import', { rules_yaml: yaml }),

  exportRules: () => api.get('/rules/export')
}

export const reportsApi = {
  getReport: (taskId, format = 'md') => api.get(`/reports/${taskId}?format=${format}`),

  downloadReport: (taskId, format = 'md') => {
    const url = `/reports/${taskId}?format=${format}`
    return window.open(url, '_blank')
  }
}

export const settingsApi = {
  getSettings: () => api.get('/settings'),

  updateSettings: (data) => api.put('/settings', data)
}

export default api
