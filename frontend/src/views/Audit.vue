<template>
  <div class="audit-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>审计任务</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            新建任务
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filter.status" placeholder="状态" clearable style="width: 120px; margin-right: 10px">
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-select v-model="filter.type" placeholder="类型" clearable style="width: 120px; margin-right: 10px">
          <el-option label="全部" value="" />
          <el-option label="代码审计" value="code" />
          <el-option label="日志审计" value="log" />
          <el-option label="流量分析" value="traffic" />
        </el-select>
        <el-button @click="fetchTasks">筛选</el-button>
      </div>

      <el-table :data="tasks" v-loading="loading" style="width: 100%; margin-top: 20px">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">{{ getTypeName(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mode" label="模式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.mode === 'ai' ? 'primary' : 'info'">
              {{ row.mode === 'ai' ? 'AI模式' : '特征匹配' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)">{{ getStatusName(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="issue_count" label="问题数" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">查看</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              :disabled="row.status === 'running'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.limit"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="fetchTasks"
        @current-change="fetchTasks"
      />
    </el-card>

    <el-dialog v-model="showUploadDialog" title="新建审计任务" width="500px">
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="审计类型">
          <el-select v-model="taskForm.type" placeholder="请选择审计类型" style="width: 100%">
            <el-option label="代码审计" value="code" />
            <el-option label="日志审计" value="log" />
            <el-option label="流量分析" value="traffic" />
          </el-select>
        </el-form-item>
        <el-form-item label="审计模式">
          <el-select v-model="taskForm.mode" placeholder="请选择审计模式" style="width: 100%">
            <el-option label="AI增强" value="ai" />
            <el-option label="特征匹配" value="feature" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
          >
            <el-button>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持代码文件、日志文件、PCAP流量包或ZIP压缩包</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTask" :loading="creating">
          创建任务
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="任务详情" width="900px">
      <div v-if="currentTask">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ currentTask.task?.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ getTypeName(currentTask.task?.type) }}</el-descriptions-item>
          <el-descriptions-item label="模式">
            {{ currentTask.task?.mode === 'ai' ? 'AI增强' : '特征匹配' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusColor(currentTask.task?.status)">
              {{ getStatusName(currentTask.task?.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件数">{{ currentTask.task?.file_count }}</el-descriptions-item>
          <el-descriptions-item label="问题数">{{ currentTask.issues?.length }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>问题列表</el-divider>

        <el-table :data="currentTask.issues" max-height="400">
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="getSeverityColor(row.severity)">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="问题标题" />
          <el-table-column prop="file_name" label="文件" width="200" />
          <el-table-column prop="line_number" label="行号" width="80" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { auditApi, reportsApi } from '../api'

const tasks = ref([])
const loading = ref(false)
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const creating = ref(false)
const currentTask = ref(null)
const uploadRef = ref(null)
const selectedFile = ref(null)

const filter = reactive({
  status: '',
  type: ''
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const taskForm = reactive({
  name: '',
  type: 'code',
  mode: 'feature'
})

onMounted(() => {
  fetchTasks()
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    }
    if (filter.status) params.status = filter.status
    if (filter.type) params.audit_type = filter.type

    const result = await auditApi.getTasks(params)
    tasks.value = result.items || result
    pagination.total = result.total || tasks.value.length
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleCreateTask = async () => {
  if (!taskForm.name) {
    ElMessage.warning('请输入任务名称')
    return
  }

  creating.value = true
  try {
    const formData = new FormData()
    formData.append('name', taskForm.name)
    formData.append('type', taskForm.type)
    formData.append('mode', taskForm.mode)
    if (selectedFile.value) {
      formData.append('file', selectedFile.value)
    }

    await auditApi.uploadTask(formData)
    ElMessage.success('任务创建成功')
    showUploadDialog.value = false
    fetchTasks()

    taskForm.name = ''
    selectedFile.value = null
  } catch (error) {
    ElMessage.error('创建任务失败')
  } finally {
    creating.value = false
  }
}

const viewDetail = async (row) => {
  try {
    currentTask.value = await auditApi.getTaskDetail(row.id)
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取任务详情失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗?', '提示', {
      type: 'warning'
    })
    await auditApi.deleteTask(row.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getTypeColor = (type) => {
  const colors = { code: 'primary', log: 'success', traffic: 'warning' }
  return colors[type] || 'info'
}

const getTypeName = (type) => {
  const names = { code: '代码审计', log: '日志审计', traffic: '流量分析' }
  return names[type] || type
}

const getStatusColor = (status) => {
  const colors = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return colors[status] || 'info'
}

const getStatusName = (status) => {
  const names = { pending: '待处理', running: '运行中', completed: '已完成', failed: '失败' }
  return names[status] || status
}

const getSeverityColor = (severity) => {
  const colors = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return colors[severity] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  align-items: center;
}
</style>
