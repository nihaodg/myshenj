<template>
  <div class="settings-page">
    <el-card>
      <template #header>
        <span>系统设置</span>
      </template>

      <el-form :model="settingsForm" label-width="140px" style="max-width: 600px">
        <el-divider content-position="left">AI 配置</el-divider>

        <el-form-item label="AI 提供商">
          <el-select v-model="settingsForm.AI_PROVIDER" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="本地 Ollama" value="ollama" />
            <el-option label="智谱 AI" value="zhipu" />
          </el-select>
        </el-form-item>

        <el-form-item label="API 地址">
          <el-input v-model="settingsForm.AI_BASE_URL" placeholder="https://api.openai.com/v1" />
        </el-form-item>

        <el-form-item label="API 密钥">
          <el-input
            v-model="settingsForm.AI_API_KEY"
            type="password"
            show-password
            placeholder="sk-..."
          />
        </el-form-item>

        <el-form-item label="模型名称">
          <el-input v-model="settingsForm.AI_MODEL" placeholder="gpt-4" />
        </el-form-item>

        <el-divider content-position="left">代理设置</el-divider>

        <el-form-item label="启用代理">
          <el-switch v-model="settingsForm.PROXY_ENABLED" />
        </el-form-item>

        <el-form-item label="代理地址" v-if="settingsForm.PROXY_ENABLED">
          <el-input v-model="settingsForm.PROXY_URL" placeholder="http://127.0.0.1:7890" />
        </el-form-item>

        <el-divider content-position="left">降级策略</el-divider>

        <el-form-item label="AI 不可用时降级">
          <el-switch v-model="settingsForm.AUTO_FALLBACK" />
          <div class="form-tip">当 AI 调用失败时，自动切换到特征匹配模式</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存设置</el-button>
          <el-button @click="fetchSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>系统信息</span>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
        <el-descriptions-item label="Python 版本">3.10+</el-descriptions-item>
        <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
        <el-descriptions-item label="部署模式">Docker</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi } from '../api'

const settingsForm = reactive({
  AI_PROVIDER: 'openai',
  AI_API_KEY: '',
  AI_BASE_URL: 'https://api.openai.com/v1',
  AI_MODEL: 'gpt-4',
  PROXY_ENABLED: false,
  PROXY_URL: '',
  AUTO_FALLBACK: true
})

const saving = ref(false)

onMounted(() => {
  fetchSettings()
})

const fetchSettings = async () => {
  try {
    const result = await settingsApi.getSettings()
    Object.assign(settingsForm, {
      AI_PROVIDER: result.AI_PROVIDER || 'openai',
      AI_API_KEY: result.AI_API_KEY || '',
      AI_BASE_URL: result.AI_BASE_URL || 'https://api.openai.com/v1',
      AI_MODEL: result.AI_MODEL || 'gpt-4',
      PROXY_ENABLED: result.PROXY_ENABLED || false,
      PROXY_URL: result.PROXY_URL || '',
      AUTO_FALLBACK: result.AUTO_FALLBACK !== false
    })
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await settingsApi.updateSettings(settingsForm)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
