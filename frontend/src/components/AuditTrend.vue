<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>审计趋势</span>
        <el-select v-model="timeRange" size="small" style="width: 120px">
          <el-option label="最近7天" :value="7" />
          <el-option label="最近30天" :value="30" />
          <el-option label="最近90天" :value="90" />
        </el-select>
      </div>
    </template>
    <div ref="trendChartRef" style="height: 300px"></div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  }
})

const trendChartRef = ref(null)
const timeRange = ref(7)
let chart = null

onMounted(() => {
  initChart()
  updateChart()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
  }
})

watch(timeRange, () => {
  updateChart()
})

watch(() => props.tasks, () => {
  updateChart()
}, { deep: true })

const initChart = () => {
  if (!trendChartRef.value) return
  chart = echarts.init(trendChartRef.value)
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  if (chart) {
    chart.resize()
  }
}

const updateChart = () => {
  if (!chart) return

  const now = new Date()
  const labels = []
  const taskData = []
  const issueData = []

  for (let i = timeRange.value - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`
    labels.push(dateStr)

    const dayStart = new Date(date.setHours(0, 0, 0, 0))
    const dayEnd = new Date(date.setHours(23, 59, 59, 999))

    const dayTasks = props.tasks.filter(t => {
      const created = new Date(t.created_at)
      return created >= dayStart && created <= dayEnd
    })

    taskData.push(dayTasks.length)

    const dayIssues = dayTasks.reduce((sum, t) => sum + (t.issue_count || 0), 0)
    issueData.push(dayIssues)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['任务数', '问题数'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: timeRange.value > 30 ? 45 : 0
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '任务',
        min: 0,
        axisLabel: { formatter: '{value}' }
      },
      {
        type: 'value',
        name: '问题',
        min: 0,
        axisLabel: { formatter: '{value}' }
      }
    ],
    series: [
      {
        name: '任务数',
        type: 'bar',
        data: taskData,
        itemStyle: { color: '#409eff' },
        barWidth: '40%'
      },
      {
        name: '问题数',
        type: 'line',
        yAxisIndex: 1,
        data: issueData,
        itemStyle: { color: '#f56c6c' },
        smooth: true,
        lineStyle: { width: 3 },
        areaStyle: {
          color: 'rgba(245, 108, 108, 0.2)'
        }
      }
    ]
  }

  chart.setOption(option)
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
