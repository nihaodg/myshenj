<template>
  <div class="attack-graph-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>攻击路径图</span>
          <el-switch v-model="showLabels" active-text="显示标签" />
        </div>
      </template>
      <div ref="graphChartRef" style="height: 450px"></div>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>攻击节点详情</span>
      </template>
      <el-table :data="selectedNodeData" v-if="selectedNodeData.length > 0" stripe>
        <el-table-column prop="id" label="节点ID" width="150" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.type)">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="details" label="详情" />
      </el-table>
      <el-empty v-else description="点击图中的节点查看详情" />
    </el-card>

    <el-card style="margin-top: 20px" v-if="attackChains.length > 0">
      <template #header>
        <span>攻击链条</span>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(chain, index) in attackChains"
          :key="index"
          :color="getChainColor(chain.severity)"
        >
          <el-card shadow="hover">
            <h4>{{ chain.step }}. {{ chain.action }}</h4>
            <p><strong>来源:</strong> {{ chain.src_ip || '未知' }} → <strong>目标:</strong> {{ chain.dst_ip || '未知' }}</p>
            <p><strong>严重程度:</strong> <el-tag :type="getSeverityType(chain.severity)">{{ chain.severity }}</el-tag></p>
            <p v-if="chain.description">{{ chain.description }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  graphData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  },
  attackChains: {
    type: Array,
    default: () => []
  }
})

const graphChartRef = ref(null)
const showLabels = ref(true)
let chart = null

const selectedNodeData = ref([])

onMounted(() => {
  initChart()
  if (props.graphData) {
    updateChart(props.graphData)
  }
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
  }
})

watch(() => props.graphData, (newData) => {
  if (newData) {
    updateChart(newData)
  }
}, { deep: true })

const initChart = () => {
  if (!graphChartRef.value) return

  chart = echarts.init(graphChartRef.value)

  chart.on('click', (params) => {
    if (params.dataType === 'node') {
      const node = props.graphData.nodes.find(n => n.id === params.data.id)
      if (node) {
        selectedNodeData.value = [{
          id: node.id,
          type: node.type || 'unknown',
          details: JSON.stringify(node, null, 2)
        }]
      }
    }
  })

  window.addEventListener('resize', handleResize)
}

const updateChart = (data) => {
  if (!chart || !data) return

  const nodes = (data.nodes || []).map(node => ({
    id: node.id || node.ip || String(node),
    name: node.ip || node.id || String(node),
    type: node.type || 'ip',
    symbolSize: node.type === 'attacker' ? 60 : node.type === 'target' ? 50 : 40,
    category: node.type === 'attacker' ? 0 : node.type === 'target' ? 1 : 2,
    itemStyle: {
      color: node.type === 'attacker' ? '#f56c6c' : 
             node.type === 'target' ? '#67c23a' : '#409eff'
    }
  }))

  const categories = [
    { name: '攻击者', itemStyle: { color: '#f56c6c' } },
    { name: '目标', itemStyle: { color: '#67c23a' } },
    { name: '中间节点', itemStyle: { color: '#409eff' } }
  ]

  const edges = (data.edges || []).map((edge, index) => ({
    source: edge.source,
    target: edge.target,
    label: {
      show: showLabels.value,
      text: edge.label || edge.protocol || '流量'
    },
    lineStyle: {
      color: edge.severity === 'high' ? '#f56c6c' : 
             edge.severity === 'medium' ? '#e6a23c' : '#909399',
      width: edge.severity === 'high' ? 3 : 2,
      curveness: 0.2
    }
  }))

  const option = {
    title: {
      text: '攻击路径拓扑图',
      subtext: '基于网络流量分析',
      left: 'center'
    },
    tooltip: {
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `<strong>${params.data.name}</strong><br/>类型: ${params.data.category === 0 ? '攻击者' : params.data.category === 1 ? '目标' : '中间节点'}`
        }
        return `${params.data.source} → ${params.data.target}<br/>${params.data.label?.text || ''}`
      }
    },
    legend: [{
      data: categories.map(c => c.name),
      left: 'left'
    }],
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      symbol: 'circle',
      label: {
        show: true,
        position: 'right',
        formatter: '{b}'
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 }
      },
      force: {
        repulsion: 200,
        edgeLength: 150,
        layoutAnimation: true
      },
      categories: categories,
      nodes: nodes,
      edges: edges
    }]
  }

  chart.setOption(option)
}

const handleResize = () => {
  if (chart) {
    chart.resize()
  }
}

watch(showLabels, () => {
  updateChart(props.graphData)
})

const getTypeTag = (type) => {
  const tags = { attacker: 'danger', target: 'success', ip: 'primary' }
  return tags[type] || 'info'
}

const getSeverityType = (severity) => {
  const types = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return types[severity?.toLowerCase()] || 'info'
}

const getChainColor = (severity) => {
  const colors = { critical: '#f56c6c', high: '#e6a23c', medium: '#409eff', low: '#67c23a' }
  return colors[severity?.toLowerCase()] || '#909399'
}
</script>

<style scoped>
.attack-graph-container {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
