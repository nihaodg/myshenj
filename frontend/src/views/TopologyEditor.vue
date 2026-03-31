<template>
  <div class="topology-editor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>攻击拓扑编辑器</span>
          <div>
            <el-button size="small" @click="resetLayout">重置布局</el-button>
            <el-button size="small" type="primary" @click="addNode">添加节点</el-button>
            <el-button size="small" type="success" @click="addEdge">添加连接</el-button>
          </div>
        </div>
      </template>

      <div class="editor-container">
        <div ref="chartRef" class="chart-container"></div>

        <div class="node-panel">
          <el-card shadow="hover">
            <template #header>节点信息</template>
            <el-form v-if="selectedNode" :model="selectedNode" label-width="80px" size="small">
              <el-form-item label="节点名称">
                <el-input v-model="selectedNode.name" @change="updateNode" />
              </el-form-item>
              <el-form-item label="节点类型">
                <el-select v-model="selectedNode.category" @change="updateNode">
                  <el-option label="攻击者" :value="0" />
                  <el-option label="目标" :value="1" />
                  <el-option label="中间节点" :value="2" />
                </el-select>
              </el-form-item>
              <el-form-item label="IP/域名">
                <el-input v-model="selectedNode.ip" @change="updateNode" />
              </el-form-item>
              <el-form-item label="描述">
                <el-input v-model="selectedNode.description" type="textarea" @change="updateNode" />
              </el-form-item>
              <el-form-item>
                <el-button type="danger" size="small" @click="deleteNode">删除节点</el-button>
              </el-form-item>
            </el-form>
            <el-empty v-else description="点击节点查看详情" />
          </el-card>

          <el-card shadow="hover" style="margin-top: 10px">
            <template #header>操作提示</template>
            <div class="tips">
              <p><el-icon><Mouse /></el-icon> 点击节点查看详情</p>
              <p><el-icon><Rank /></el-icon> 拖动节点调整位置</p>
              <p><el-icon><ZoomIn /></el-icon> 滚轮缩放视图</p>
              <p><el-icon><FullScreen /></el-icon> 拖动空白处平移</p>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="showAddEdgeDialog" title="添加连接" width="400px">
      <el-form :model="edgeForm" label-width="80px">
        <el-form-item label="源节点">
          <el-select v-model="edgeForm.source" placeholder="选择源节点">
            <el-option
              v-for="node in nodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标节点">
          <el-select v-model="edgeForm.target" placeholder="选择目标节点">
            <el-option
              v-for="node in nodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="连接类型">
          <el-input v-model="edgeForm.label" placeholder="如: TCP连接、HTTP请求" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="edgeForm.severity">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddEdgeDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddEdge">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddNodeDialog" title="添加节点" width="400px">
      <el-form :model="nodeForm" label-width="80px">
        <el-form-item label="节点名称">
          <el-input v-model="nodeForm.name" placeholder="如: 攻击者A" />
        </el-form-item>
        <el-form-item label="节点类型">
          <el-select v-model="nodeForm.category">
            <el-option label="攻击者" :value="0" />
            <el-option label="目标" :value="1" />
            <el-option label="中间节点" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP/域名">
          <el-input v-model="nodeForm.ip" placeholder="如: 192.168.1.100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddNodeDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddNode">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const chartRef = ref(null)
let chart = null

const nodes = ref([
  { id: 'attacker1', name: '攻击者', category: 0, ip: '203.0.113.50', x: 100, y: 200, description: '外部攻击源' },
  { id: 'webserver', name: 'Web服务器', category: 1, ip: '192.168.1.10', x: 400, y: 200, description: '目标Web服务器' },
  { id: 'dbserver', name: '数据库服务器', category: 1, ip: '192.168.1.20', x: 700, y: 200, description: '核心数据库' },
  { id: 'internal', name: '内网主机', category: 2, ip: '192.168.1.100', x: 400, y: 400, description: '已被入侵的内网主机' }
])

const edges = ref([
  { source: 'attacker1', target: 'webserver', label: 'SQL注入', severity: 'high' },
  { source: 'webserver', target: 'dbserver', label: '数据库查询', severity: 'medium' },
  { source: 'attacker1', target: 'internal', label: '恶意软件', severity: 'high' },
  { source: 'internal', target: 'dbserver', label: '横向移动', severity: 'high' }
])

const selectedNode = ref(null)
const showAddEdgeDialog = ref(false)
const showAddNodeDialog = ref(false)

const edgeForm = reactive({
  source: '',
  target: '',
  label: '',
  severity: 'medium'
})

const nodeForm = reactive({
  name: '',
  category: 0,
  ip: ''
})

const categories = [
  { name: '攻击者', itemStyle: { color: '#f56c6c' } },
  { name: '目标', itemStyle: { color: '#67c23a' } },
  { name: '中间节点', itemStyle: { color: '#409eff' } }
]

onMounted => {
  initChart()
}

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
  }
})

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()

  chart.on('click', (params) => {
    if (params.dataType === 'node') {
      const node = nodes.value.find(n => n.id === params.data.id)
      if (node) {
        selectedNode.value = { ...node }
      }
    }
  })

  chart.on('mouseup', (params) => {
    if (params.dataType === 'node' && params.data.x && params.data.y) {
      const node = nodes.value.find(n => n.id === params.data.id)
      if (node) {
        node.x = params.data.x
        node.y = params.data.y
      }
    }
  })

  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  if (chart) {
    chart.resize()
  }
}

const updateChart = () => {
  if (!chart) return

  const option = {
    title: {
      text: '攻击拓扑图',
      subtext: '拖动节点调整位置',
      left: 'center'
    },
    tooltip: {
      formatter: (params) => {
        if (params.dataType === 'node') {
          const node = nodes.value.find(n => n.id === params.data.id)
          return `<strong>${params.data.name}</strong><br/>IP: ${node?.ip || 'N/A'}<br/>${node?.description || ''}`
        }
        return `${params.data.source} → ${params.data.target}<br/>${params.data.label || ''}`
      }
    },
    legend: {
      data: categories.map(c => c.name),
      left: 'left'
    },
    series: [{
      type: 'graph',
      layout: 'none',
      draggable: true,
      roam: true,
      symbol: 'circle',
      symbolSize: 50,
      label: {
        show: true,
        position: 'bottom',
        formatter: '{b}'
      },
      edgeSymbol: ['circle', 'arrow'],
      edgeSymbolSize: [8, 10],
      categories: categories,
      nodes: nodes.value.map(n => ({
        id: n.id,
        name: n.name,
        category: n.category,
        x: n.x,
        y: n.y,
        ip: n.ip,
        description: n.description,
        itemStyle: {
          color: categories[n.category].itemStyle.color
        }
      })),
      edges: edges.value.map(e => ({
        source: e.source,
        target: e.target,
        label: { show: true, formatter: e.label },
        lineStyle: {
          color: e.severity === 'high' ? '#f56c6c' : e.severity === 'medium' ? '#e6a23c' : '#67c23a',
          width: e.severity === 'high' ? 3 : 2,
          curveness: 0.2
        }
      })),
      lineStyle: {
        width: 2,
        curveness: 0.2
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 }
      }
    }]
  }

  chart.setOption(option, true)
}

const updateNode = () => {
  const index = nodes.value.findIndex(n => n.id === selectedNode.value.id)
  if (index !== -1) {
    nodes.value[index] = { ...selectedNode.value }
    updateChart()
  }
}

const deleteNode = () => {
  const index = nodes.value.findIndex(n => n.id === selectedNode.value.id)
  if (index !== -1) {
    nodes.value.splice(index, 1)
    edges.value = edges.value.filter(e => e.source !== selectedNode.value.id && e.target !== selectedNode.value.id)
    selectedNode.value = null
    updateChart()
    ElMessage.success('节点已删除')
  }
}

const resetLayout = () => {
  nodes.value = [
    { id: 'attacker1', name: '攻击者', category: 0, ip: '203.0.113.50', x: 100, y: 200, description: '外部攻击源' },
    { id: 'webserver', name: 'Web服务器', category: 1, ip: '192.168.1.10', x: 400, y: 200, description: '目标Web服务器' },
    { id: 'dbserver', name: '数据库服务器', category: 1, ip: '192.168.1.20', x: 700, y: 200, description: '核心数据库' },
    { id: 'internal', name: '内网主机', category: 2, ip: '192.168.1.100', x: 400, y: 400, description: '已被入侵的内网主机' }
  ]
  edges.value = [
    { source: 'attacker1', target: 'webserver', label: 'SQL注入', severity: 'high' },
    { source: 'webserver', target: 'dbserver', label: '数据库查询', severity: 'medium' },
    { source: 'attacker1', target: 'internal', label: '恶意软件', severity: 'high' },
    { source: 'internal', target: 'dbserver', label: '横向移动', severity: 'high' }
  ]
  selectedNode.value = null
  updateChart()
  ElMessage.success('布局已重置')
}

const addNode = () => {
  nodeForm.name = ''
  nodeForm.category = 2
  nodeForm.ip = ''
  showAddNodeDialog.value = true
}

const confirmAddNode = () => {
  if (!nodeForm.name) {
    ElMessage.warning('请输入节点名称')
    return
  }

  const id = 'node_' + Date.now()
  const newNode = {
    id,
    name: nodeForm.name,
    category: nodeForm.category,
    ip: nodeForm.ip,
    x: 400 + Math.random() * 100 - 50,
    y: 300 + Math.random() * 100 - 50,
    description: ''
  }

  nodes.value.push(newNode)
  showAddNodeDialog.value = false
  updateChart()
  ElMessage.success('节点已添加')
}

const addEdge = () => {
  edgeForm.source = ''
  edgeForm.target = ''
  edgeForm.label = ''
  edgeForm.severity = 'medium'
  showAddEdgeDialog.value = true
}

const confirmAddEdge = () => {
  if (!edgeForm.source || !edgeForm.target) {
    ElMessage.warning('请选择源节点和目标节点')
    return
  }

  if (edgeForm.source === edgeForm.target) {
    ElMessage.warning('源节点和目标节点不能相同')
    return
  }

  const exists = edges.value.some(
    e => e.source === edgeForm.source && e.target === edgeForm.target
  )

  if (exists) {
    ElMessage.warning('该连接已存在')
    return
  }

  edges.value.push({
    source: edgeForm.source,
    target: edgeForm.target,
    label: edgeForm.label || '连接',
    severity: edgeForm.severity
  })

  showAddEdgeDialog.value = false
  updateChart()
  ElMessage.success('连接已添加')
}
</script>

<style scoped>
.topology-editor {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-container {
  display: flex;
  height: 600px;
}

.chart-container {
  flex: 1;
  height: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.node-panel {
  width: 280px;
  margin-left: 20px;
}

.tips p {
  margin: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}
</style>
