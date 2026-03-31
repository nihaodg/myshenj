<template>
  <div class="monitor-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon total">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_alerts }}</div>
            <div class="stat-label">总告警数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon high">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.high_severity }}</div>
            <div class="stat-label">高危告警</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon blocked">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ blockedCount }}</div>
            <div class="stat-label">已封锁IP</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon running">
            <el-icon><SuccessFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ isRunning ? '运行中' : '已停止' }}</div>
            <div class="stat-label">监控状态</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>告警趋势</span>
          </template>
          <div ref="alertTrendChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>告警类型分布</span>
          </template>
          <div ref="alertTypeChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近告警</span>
          </template>
          <el-table :data="recentAlerts" style="width: 100%">
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="severity" label="严重程度" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="src_ip" label="来源IP" width="140" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="blockIP(row.src_ip)" v-if="row.src_ip">
                  封锁
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>已封锁IP</span>
              <el-button size="small" type="primary" @click="refreshBlocked">刷新</el-button>
            </div>
          </template>
          <el-table :data="blockedIPs" style="width: 100%">
            <el-table-column prop="ip_address" label="IP 地址" />
            <el-table-column prop="reason" label="封锁原因" />
            <el-table-column prop="blocked_at" label="封锁时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.blocked_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="success" @click="unblockIP(row.ip_address)">
                  解封
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>封锁新IP</span>
          </template>
          <el-form :inline="true" :model="blockForm">
            <el-form-item label="IP 地址">
              <el-input v-model="blockForm.ip_address" placeholder="如: 192.168.1.100" style="width: 200px" />
            </el-form-item>
            <el-form-item label="封锁原因">
              <el-input v-model="blockForm.reason" placeholder="可选" style="width: 200px" />
            </el-form-item>
            <el-form-item label="持续时间">
              <el-select v-model="blockForm.duration" style="width: 150px">
                <el-option label="1小时" :value="1" />
                <el-option label="6小时" :value="6" />
                <el-option label="24小时" :value="24" />
                <el-option label="7天" :value="168" />
                <el-option label="永久" :value="0" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="danger" @click="handleBlockIP">封锁此IP</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { defenseApi, alertsApi } from '../api'

const alertTrendChart = ref(null)
const alertTypeChart = ref(null)
let trendChart = null
let typeChart = null
let refreshTimer = null

const stats = reactive({
  total_alerts: 0,
  high_severity: 0,
  medium: 0
})

const recentAlerts = ref([])
const blockedIPs = ref([])
const blockedCount = ref(0)
const isRunning = ref(true)

const blockForm = reactive({
  ip_address: '',
  reason: '',
  duration: 24
})

onMounted(() => {
  initCharts()
  fetchData()
  fetchBlockedIPs()

  refreshTimer = setInterval(() => {
    fetchData()
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

const initCharts = () => {
  if (alertTrendChart.value) {
    trendChart = echarts.init(alertTrendChart.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['告警数量'] },
      xAxis: {
        type: 'category',
        data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '现在']
      },
      yAxis: [{ type: 'value' }],
      series: [{
        name: '告警数量',
        type: 'line',
        data: [12, 25, 18, 35, 28, 42, 38],
        smooth: true,
        itemStyle: { color: '#409eff' }
      }]
    })
  }

  if (alertTypeChart.value) {
    typeChart = echarts.init(alertTypeChart.value)
    typeChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 10 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: 35, name: 'SQL注入', itemStyle: { color: '#f56c6c' } },
          { value: 25, name: 'XSS攻击', itemStyle: { color: '#e6a23c' } },
          { value: 20, name: '暴力破解', itemStyle: { color: '#409eff' } },
          { value: 15, name: '端口扫描', itemStyle: { color: '#67c23a' } },
          { value: 5, name: '其他', itemStyle: { color: '#909399' } }
        ]
      }]
    })
  }
}

const fetchData = async () => {
  try {
    const [alertsRes, statsRes] = await Promise.all([
      alertsApi.getAlerts(),
      alertsApi.getAlertStats()
    ])

    recentAlerts.value = Array.isArray(alertsRes) ? alertsRes.slice(0, 10) : []
    stats.total_alerts = statsRes.total || 0
    stats.high_severity = (statsRes.severity?.high || 0) + (statsRes.severity?.critical || 0)
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

const fetchBlockedIPs = async () => {
  try {
    const res = await defenseApi.getBlocked()
    blockedIPs.value = res.blocked_ips || []
    blockedCount.value = blockedIPs.value.length
  } catch (error) {
    console.error('获取封锁列表失败:', error)
  }
}

const refreshBlocked = () => {
  fetchBlockedIPs()
  ElMessage.success('已刷新')
}

const blockIP = async (ip) => {
  if (!ip) return
  try {
    await defenseApi.blockIP(ip, '手动封锁', 24)
    ElMessage.success(`IP ${ip} 已封锁`)
    fetchBlockedIPs()
  } catch (error) {
    ElMessage.error('封锁失败')
  }
}

const unblockIP = async (ip) => {
  try {
    await defenseApi.unblockIP(ip)
    ElMessage.success(`IP ${ip} 已解封`)
    fetchBlockedIPs()
  } catch (error) {
    ElMessage.error('解封失败')
  }
}

const handleBlockIP = async () => {
  if (!blockForm.ip_address) {
    ElMessage.warning('请输入IP地址')
    return
  }
  try {
    await defenseApi.blockIP(blockForm.ip_address, blockForm.reason, blockForm.duration)
    ElMessage.success(`IP ${blockForm.ip_address} 已封锁`)
    blockForm.ip_address = ''
    blockForm.reason = ''
    fetchBlockedIPs()
  } catch (error) {
    ElMessage.error('封锁失败')
  }
}

const getSeverityType = (severity) => {
  const types = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return types[severity?.toLowerCase()] || 'info'
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
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
.stat-icon.high { background-color: #fde2e2; color: #f56c6c; }
.stat-icon.blocked { background-color: #fef0e6; color: #e6a23c; }
.stat-icon.running { background-color: #e6f7ed; color: #67c23a; }

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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
