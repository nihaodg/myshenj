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

export const alertsApi = {
  getAlerts: (limit = 100) => api.get(`/alerts?limit=${limit}`),
  
  getAlertStats: () => api.get('/alerts/stats'),
  
  updateConfig: (config) => api.post('/alerts/config', config),
  
  testAlert: () => api.post('/alerts/test')
}

export const defenseApi = {
  blockIP: (ip, reason, duration) => 
    api.post('/defense/block', { ip_address: ip, reason, duration_hours: duration }),
  
  unblockIP: (ip) => 
    api.post('/defense/unblock', { ip_address: ip }),
  
  getBlocked: () => api.get('/defense/blocked'),
  
  checkIP: (ip) => api.get(`/defense/check/${ip}`)
}

export const mitreApi = {
  getTactics: () => api.get('/mitre/tactics'),
  
  getAllMappings: () => api.get('/mitre/all'),
  
  getTacticDetail: (tacticId) => api.get(`/mitre/tactics/${tacticId}`)
}

export default api
