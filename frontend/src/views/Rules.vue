<template>
  <div class="rules-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>规则管理</span>
          <div>
            <el-button @click="handleExport" style="margin-right: 10px">导出规则</el-button>
            <el-button type="primary" @click="showEditor(null)">
              <el-icon><Plus /></el-icon>
              新建规则
            </el-button>
          </div>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filter.severity" placeholder="严重程度" clearable style="width: 120px; margin-right: 10px">
          <el-option label="全部" value="" />
          <el-option label="Critical" value="critical" />
          <el-option label="High" value="high" />
          <el-option label="Medium" value="medium" />
          <el-option label="Low" value="low" />
        </el-select>
        <el-select v-model="filter.language" placeholder="语言" clearable style="width: 120px; margin-right: 10px">
          <el-option label="全部" value="" />
          <el-option label="Python" value="python" />
          <el-option label="JavaScript" value="javascript" />
          <el-option label="Java" value="java" />
          <el-option label="Go" value="go" />
          <el-option label="通用" value="" />
        </el-select>
        <el-button @click="fetchRules">筛选</el-button>
      </div>

      <el-table :data="rules" v-loading="loading" style="width: 100%; margin-top: 20px">
        <el-table-column prop="rule_id" label="规则ID" width="150" />
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityColor(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100">
          <template #default="{ row }">
            {{ row.language || '通用' }}
          </template>
        </el-table-column>
        <el-table-column prop="pattern" label="匹配模式" width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.pattern" placement="top">
              <span class="pattern-text">{{ row.pattern.substring(0, 50) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditor(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
        @size-change="fetchRules"
        @current-change="fetchRules"
      />
    </el-card>

    <el-dialog v-model="showDialog" :title="isEditing ? '编辑规则' : '新建规则'" width="700px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则ID" required>
          <el-input v-model="ruleForm.rule_id" :disabled="isEditing" placeholder="如: SQLI-001" />
        </el-form-item>
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" placeholder="如: SQL注入检测" />
        </el-form-item>
        <el-form-item label="严重程度" required>
          <el-select v-model="ruleForm.severity" style="width: 100%">
            <el-option label="Critical" value="critical" />
            <el-option label="High" value="high" />
            <el-option label="Medium" value="medium" />
            <el-option label="Low" value="low" />
            <el-option label="Info" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="编程语言">
          <el-select v-model="ruleForm.language" placeholder="留空表示通用" clearable style="width: 100%">
            <el-option label="Python" value="python" />
            <el-option label="JavaScript" value="javascript" />
            <el-option label="Java" value="java" />
            <el-option label="Go" value="go" />
            <el-option label="C/C++" value="c" />
            <el-option label="通用" value="" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配模式" required>
          <el-input
            v-model="ruleForm.pattern"
            type="textarea"
            :rows="3"
            placeholder="正则表达式，如: (?i)exec\s*\("
          />
        </el-form-item>
        <el-form-item label="提示信息" required>
          <el-input
            v-model="ruleForm.message"
            type="textarea"
            :rows="2"
            placeholder="检测到问题时显示的消息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { rulesApi } from '../api'

const rules = ref([])
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const filter = reactive({
  severity: '',
  language: ''
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const ruleForm = reactive({
  rule_id: '',
  name: '',
  severity: 'medium',
  language: '',
  pattern: '',
  message: '',
  enabled: true
})

onMounted(() => {
  fetchRules()
})

const fetchRules = async () => {
  loading.value = true
  try {
    const params = { skip: (pagination.page - 1) * pagination.limit, limit: pagination.limit }
    if (filter.severity) params.severity = filter.severity
    if (filter.language) params.language = filter.language

    const result = await rulesApi.getRules(params)
    rules.value = result
    pagination.total = result.length
  } catch (error) {
    ElMessage.error('获取规则列表失败')
  } finally {
    loading.value = false
  }
}

const showEditor = (row) => {
  if (row) {
    isEditing.value = true
    editingId.value = row.id
    Object.assign(ruleForm, {
      rule_id: row.rule_id,
      name: row.name,
      severity: row.severity,
      language: row.language || '',
      pattern: row.pattern,
      message: row.message,
      enabled: row.enabled
    })
  } else {
    isEditing.value = false
    editingId.value = null
    Object.assign(ruleForm, {
      rule_id: '',
      name: '',
      severity: 'medium',
      language: '',
      pattern: '',
      message: '',
      enabled: true
    })
  }
  showDialog.value = true
}

const handleSave = async () => {
  if (!ruleForm.rule_id || !ruleForm.name || !ruleForm.pattern || !ruleForm.message) {
    ElMessage.warning('请填写所有必填字段')
    return
  }

  saving.value = true
  try {
    if (isEditing.value) {
      await rulesApi.updateRule(editingId.value, ruleForm)
      ElMessage.success('规则更新成功')
    } else {
      await rulesApi.createRule(ruleForm)
      ElMessage.success('规则创建成功')
    }
    showDialog.value = false
    fetchRules()
  } catch (error) {
    ElMessage.error(error.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleToggle = async (row) => {
  try {
    await rulesApi.updateRule(row.id, { enabled: row.enabled })
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
    row.enabled = !row.enabled
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该规则吗?', '提示', { type: 'warning' })
    await rulesApi.deleteRule(row.id)
    ElMessage.success('删除成功')
    fetchRules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = async () => {
  try {
    const yaml = await rulesApi.exportRules()
    const blob = new Blob([yaml], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'rules.yaml'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const getSeverityColor = (severity) => {
  const colors = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return colors[severity] || 'info'
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

.pattern-text {
  font-family: monospace;
  font-size: 12px;
}
</style>
