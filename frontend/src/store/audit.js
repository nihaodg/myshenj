import { defineStore } from 'pinia'
import { auditApi } from '../api'

export const useAuditStore = defineStore('audit', {
  state: () => ({
    tasks: [],
    currentTask: null,
    statistics: {
      total_tasks: 0,
      completed_tasks: 0,
      total_issues: 0,
      high_issues: 0
    },
    loading: false
  }),

  actions: {
    async fetchTasks(params = {}) {
      this.loading = true
      try {
        const result = await auditApi.getTasks(params)
        this.tasks = result.items || result
      } finally {
        this.loading = false
      }
    },

    async fetchStatistics() {
      try {
        const stats = await auditApi.getStatistics()
        this.statistics = stats
      } catch (error) {
        console.error('Failed to fetch statistics:', error)
      }
    },

    async fetchTaskDetail(taskId) {
      try {
        const result = await auditApi.getTaskDetail(taskId)
        this.currentTask = result
        return result
      } catch (error) {
        console.error('Failed to fetch task detail:', error)
        throw error
      }
    },

    async deleteTask(taskId) {
      await auditApi.deleteTask(taskId)
      this.tasks = this.tasks.filter(t => t.id !== taskId)
    }
  }
})
