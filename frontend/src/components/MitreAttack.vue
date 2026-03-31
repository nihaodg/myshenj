<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>告警与攻击分析</span>
        <el-tag type="info">MITRE ATT&CK</el-tag>
      </div>
    </template>

    <el-row :gutter="20">
      <el-col :span="12">
        <div ref="mitreChartRef" style="height: 300px"></div>
      </el-col>
      <el-col :span="12">
        <el-table :data="issueWithTactics" size="small" max-height="300">
          <el-table-column prop="rule_name" label="问题" min-width="150" />
          <el-table-column prop="tactic_name" label="战术分类" width="120">
            <template #default="{ row }">
              <el-tag size="small" type="primary">{{ row.tactic_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="technique_id" label="技术ID" width="100">
            <template #default="{ row }">
              <a v-if="row.mitre_url" :href="row.mitre_url" target="_blank" class="mitre-link">
                {{ row.technique_id }}
              </a>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="getSeverityType(row.severity)">
                {{ row.severity }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <el-divider>攻击战术分布</el-divider>

    <div class="tactics-grid">
      <div
        v-for="tactic in tacticStats"
        :key="tactic.id"
        class="tactic-item"
      >
        <div class="tactic-name">{{ tactic.name }}</div>
        <el-progress
          :percentage="tactic.percentage"
          :color="tactic.color"
          :stroke-width="20"
        />
        <div class="tactic-count">{{ tactic.count }} 个问题</div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  issues: {
    type: Array,
    default: () => []
  },
  mitreMappings: {
    type: Object,
    default: () => ({})
  }
})

const mitreChartRef = ref(null)
let chart = null

const tacticColors = {
  'initial_access': '#f56c6c',
  'execution': '#e6a23c',
  'persistence': '#909399',
  'privilege_escalation': '#67c23a',
  'defense_evasion': '#409eff',
  'credential_access': '#9c27b0',
  'discovery': '#00bcd4',
  'lateral_movement': '#ff5722',
  'collection': '#795548',
  'command_and_control': '#607d8b',
  'exfiltration': '#3f51b5',
  'impact': '#dc3545'
}

const issueWithTactics = computed(() => {
  return props.issues.map(issue => {
    const ruleId = issue.rule_id || ''
    const mapping = props.mitreMappings[ruleId] || props.mitreMappings[issue.rule_name] || {}
    
    let tacticName = mapping.tactic_name || '未知战术'
    let tacticId = mapping.tactic_id || ''
    let techniqueId = mapping.technique_id || ''
    let mitreUrl = techniqueId ? `https://attack.mitre.org/techniques/${techniqueId}/` : ''

    if (!tacticName || tacticName === '未知战术') {
      for (const [key, val] of Object.entries(props.mitreMappings)) {
        if (ruleId.toUpperCase().includes(key.toUpperCase())) {
          tacticName = val.tactic_name || '未知战术'
          tacticId = val.tactic_id || ''
          techniqueId = val.technique_id || ''
          mitreUrl = techniqueId ? `https://attack.mitre.org/techniques/${techniqueId}/` : ''
          break
        }
      }
    }

    return {
      ...issue,
      tactic_name: tacticName,
      tactic_id: tacticId,
      technique_id: techniqueId,
      mitre_url: mitreUrl
    }
  })
})

const tacticStats = computed(() => {
  const counts = {}
  
  issueWithTactics.value.forEach(issue => {
    const tid = issue.tactic_id || 'unknown'
    if (!counts[tid]) {
      counts[tid] = {
        id: tid,
        name: issue.tactic_name || '未知战术',
        count: 0,
        color: tacticColors[tid] || '#909399'
      }
    }
    counts[tid].count++
  })

  const total = props.issues.length || 1
  return Object.values(counts)
    .map(t => ({
      ...t,
      percentage: Math.round((t.count / total) * 100)
    }))
    .sort((a, b) => b.count - a.count)
})

onMounted(() => {
  initChart()
})

watch(() => props.issues, () => {
  if (chart) {
    updateChart()
  }
}, { deep: true })

const initChart = () => {
  if (!mitreChartRef.value) return
  
  chart = echarts.init(mitreChartRef.value)
  updateChart()

  window.addEventListener('resize', () => {
    if (chart) chart.resize()
  })
}

const updateChart = () => {
  if (!chart) return

  const data = tacticStats.value.map(t => ({
    name: t.name,
    value: t.count,
    itemStyle: { color: t.color }
  }))

  chart.setOption({
    title: {
      text: '攻击战术分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        show: true,
        formatter: '{b}: {d}%'
      }
    }]
  })
}

const getSeverityType = (severity) => {
  const types = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return types[severity?.toLowerCase()] || 'info'
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mitre-link {
  color: #409eff;
  text-decoration: none;
}

.mitre-link:hover {
  text-decoration: underline;
}

.tactics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.tactic-item {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.tactic-name {
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.tactic-count {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}
</style>
