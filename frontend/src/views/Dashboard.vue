<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon total">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ statistics.total_tasks }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon completed">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ statistics.completed_tasks }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon issues">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ statistics.total_issues }}</div>
            <div class="stat-label">发现问题</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon high">
            <el-icon><WarnTriangleFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ statistics.high_issues }}</div>
            <div class="stat-label">高危问题</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>审计任务趋势</span>
          </template>
          <div ref="trendChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>问题类型分布</span>
          </template>
          <div ref="pieChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最近任务</span>
          </template>
          <el-table :data="recentTasks" style="width: 100%">
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getTypeColor(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="mode" label="模式" width="100">
              <template #default="{ row }">
                <el-tag>{{ row.mode === 'ai' ? 'AI模式' : '特征匹配' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusColor(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="issue_count" label="问题数" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuditStore } from '../store/audit'
import * as echarts from 'echarts'

const auditStore = useAuditStore()
const trendChartRef = ref(null)
const pieChartRef = ref(null)

const statistics = computed(() => auditStore.statistics)
const recentTasks = computed(() => auditStore.tasks.slice(0, 5))

onMounted(async () => {
  await auditStore.fetchStatistics()
  await auditStore.fetchTasks({ limit: 5 })

  if (trendChartRef.value) {
    const trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['任务数', '问题数'] },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      },
      yAxis: [{ type: 'value' }],
      series: [
        {
          name: '任务数',
          type: 'line',
          data: [2, 4, 3, 5, 6, 7, 5],
          smooth: true,
          itemStyle: { color: '#409eff' }
        },
        {
          name: '问题数',
          type: 'line',
          data: [5, 12, 8, 15, 20, 18, 25],
          smooth: true,
          itemStyle: { color: '#f56c6c' }
        }
      ]
    })
  }

  if (pieChartRef.value) {
    const pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 10, left: 'center' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold' }
          },
          data: [
            { value: 35, name: 'SQL注入', itemStyle: { color: '#f56c6c' } },
            { value: 25, name: '硬编码密钥', itemStyle: { color: '#e6a23c' } },
            { value: 20, name: 'XSS', itemStyle: { color: '#409eff' } },
            { value: 15, name: '其他', itemStyle: { color: '#67c23a' } }
          ]
        }
      ]
    })
  }
})

const getTypeColor = (type) => {
  const colors = { code: 'primary', log: 'success', traffic: 'warning' }
  return colors[type] || 'info'
}

const getStatusColor = (status) => {
  const colors = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return colors[status] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-right: 15px;
}

.stat-icon.total { background-color: #e6f0ff; color: #409eff; }
.stat-icon.completed { background-color: #e6f7ed; color: #67c23a; }
.stat-icon.issues { background-color: #fef0e6; color: #e6a23c; }
.stat-icon.high { background-color: #fde2e2; color: #f56c6c; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}
</style>
