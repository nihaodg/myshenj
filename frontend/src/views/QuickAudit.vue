<template>
  <div class="quick-audit">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>代码输入</span>
              <el-select v-model="language" size="small" style="width: 120px">
                <el-option label="自动检测" value="auto" />
                <el-option label="Python" value="python" />
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Java" value="java" />
                <el-option label="Go" value="go" />
                <el-option label="PHP" value="php" />
                <el-option label="C/C++" value="c" />
              </el-select>
            </div>
          </template>
          
          <el-input
            v-model="code"
            type="textarea"
            :rows="20"
            placeholder="粘贴需要审计的代码片段..."
            class="code-input"
          />
          
          <div class="action-bar">
            <el-button type="primary" @click="handleAudit" :loading="loading" size="large">
              开始审计
            </el-button>
            <el-button @click="handleClear" size="large">清空</el-button>
            <el-button @click="handleSample" size="large">加载示例</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card v-loading="loading">
          <template #header>
            <span>审计结果</span>
          </template>
          
          <div v-if="!results.length && !loading" class="empty-result">
            <el-empty description="暂无审计结果" />
          </div>
          
          <div v-else class="results-container">
            <el-alert
              :title="`发现 ${results.length} 个问题`"
              :type="results.length > 0 ? 'warning' : 'success'"
              :closable="false"
              style="margin-bottom: 15px"
            />
            
            <div v-for="(item, index) in results" :key="index" class="result-item">
              <el-card shadow="hover" class="issue-card">
                <template #header>
                  <div class="issue-header">
                    <el-tag :type="getSeverityType(item.severity)" size="small">
                      {{ item.severity.toUpperCase() }}
                    </el-tag>
                    <span class="issue-title">{{ item.title }}</span>
                    <el-tag v-if="item.cwe_id" size="small" type="info">
                      <a :href="'https://cwe.mitre.org/data/definitions/' + item.cwe_id.replace('CWE-', '') + '.html'" target="_blank" class="cwe-link">
                        {{ item.cwe_id }}
                      </a>
                    </el-tag>
                  </div>
                </template>
                
                <div class="issue-content">
                  <div class="issue-section">
                    <strong>漏洞类型：</strong>
                    <span>{{ item.category }}</span>
                  </div>
                  
                  <div class="issue-section">
                    <strong>描述：</strong>
                    <span>{{ item.description }}</span>
                  </div>
                  
                  <div class="issue-section" v-if="item.match_line">
                    <strong>匹配代码：</strong>
                    <pre class="code-snippet">{{ item.match_line }}</pre>
                  </div>
                  
                  <div class="issue-section">
                    <strong>修复建议：</strong>
                    <span class="recommendation">{{ item.recommendation }}</span>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>支持的检测类型</span>
          </template>
          <el-tag
            v-for="type in supportedTypes"
            :key="type.name"
            :type="type.level === 'high' ? 'danger' : type.level === 'medium' ? 'warning' : 'info'"
            style="margin: 5px"
          >
            {{ type.name }}
          </el-tag>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const code = ref('')
const language = ref('auto')
const loading = ref(false)
const results = ref([])

const supportedTypes = [
  { name: 'SQL注入', level: 'high' },
  { name: '命令注入', level: 'high' },
  { name: '硬编码密钥', level: 'high' },
  { name: 'XSS', level: 'medium' },
  { name: '路径遍历', level: 'medium' },
  { name: '不安全的随机数', level: 'medium' },
  { name: '日志注入', level: 'low' },
  { name: '危险函数eval', level: 'medium' },
  { name: '硬编码密码', level: 'high' },
  { name: 'SSRF', level: 'medium' },
  { name: 'XXE', level: 'high' }
]

const detectionRules = [
  {
    pattern: /(?i)(cursor\.execute|executemany)\s*\([^)]*%s/,
    title: 'SQL注入漏洞',
    category: 'SQL Injection',
    cwe_id: 'CWE-89',
    severity: 'high',
    description: '检测到使用SQL占位的查询，可能导致SQL注入',
    recommendation: '使用参数化查询（prepared statements）替代字符串拼接'
  },
  {
    pattern: /(?i)(exec|execute)\s*\(.*?(?:select|insert|update|delete)\s*/,
    title: 'SQL注入风险',
    category: 'SQL Injection',
    cwe_id: 'CWE-89',
    severity: 'high',
    description: '检测到使用字符串拼接执行SQL语句',
    recommendation: '使用ORM或参数化查询'
  },
  {
    pattern: /(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*["'][a-zA-Z0-9]{16,}/,
    title: '硬编码密钥',
    category: 'Hardcoded Secret',
    cwe_id: 'CWE-798',
    severity: 'high',
    description: '检测到硬编码的API密钥或访问令牌',
    recommendation: '使用环境变量或安全的密钥管理服务'
  },
  {
    pattern: /\beval\s*\(/,
    title: 'eval危险函数',
    category: 'Dangerous Function',
    cwe_id: 'CWE-95',
    severity: 'high',
    description: '检测到eval使用，可能导致代码注入',
    recommendation: '避免使用eval，使用更安全的替代方案'
  },
  {
    pattern: /\.innerHTML\s*=/,
    title: 'XSS漏洞',
    category: 'Cross-Site Scripting',
    cwe_id: 'CWE-79',
    severity: 'medium',
    description: '检测到innerHTML直接赋值，可能导致XSS攻击',
    recommendation: '使用textContent或对输入进行HTML转义'
  },
  {
    pattern: /(?i)(password|passwd|pwd)\s*=\s*["'][^"']{4,}/,
    title: '硬编码密码',
    category: 'Hardcoded Password',
    cwe_id: 'CWE-259',
    severity: 'high',
    description: '检测到硬编码密码',
    recommendation: '使用环境变量或配置中心管理密码'
  },
  {
    pattern: /random\.(random|randint|choice)\s*\(/,
    title: '不安全的随机数',
    category: 'Insecure Randomness',
    cwe_id: 'CWE-338',
    severity: 'medium',
    description: '使用random模块生成安全敏感数据',
    recommendation: '使用secrets模块生成安全随机数'
  },
  {
    pattern: /os\.system\s*\(|subprocess\.\w+\s*\([^)]*shell\s*=\s*True/,
    title: '命令注入',
    category: 'Command Injection',
    cwe_id: 'CWE-78',
    severity: 'critical',
    description: '检测到可能的命令注入风险',
    recommendation: '避免shell=True，使用参数列表传递命令'
  },
  {
    pattern: /(?i)(log|logger|print)\s*\(.*?(?:\\n|\\r|%0a|%0d)/,
    title: '日志注入',
    category: 'Log Injection',
    cwe_id: 'CWE-117',
    severity: 'low',
    description: '检测到可能的日志注入风险',
    recommendation: '对用户输入进行日志输出时进行转义'
  },
  {
    pattern: /open\s*\([^)]*\+\s*(?:request\.|os\.path\.)/,
    title: '路径遍历',
    category: 'Path Traversal',
    cwe_id: 'CWE-22',
    severity: 'medium',
    description: '检测到可能的路径遍历漏洞',
    recommendation: '对用户输入进行路径规范化验证'
  },
  {
    pattern: /xml\.parse|dtd|entity/i,
    title: 'XXE风险',
    category: 'XML External Entity',
    cwe_id: 'CWE-611',
    severity: 'high',
    description: '检测到可能的XXE漏洞',
    recommendation: '禁用XML外部实体解析，使用安全的XML解析器'
  },
  {
    pattern: /requests\.get|urllib\.open|httpx\.get/i,
    title: 'SSRF风险',
    category: 'Server-Side Request Forgery',
    cwe_id: 'CWE-918',
    severity: 'medium',
    description: '检测到可能的SSRF漏洞',
    recommendation: '对URL进行验证，禁止访问内网地址'
  }
]

const sampleCode = `import sqlite3
import random

def login(username, password):
    # 硬编码密码示例
    admin_password = "admin123"
    
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    # SQL注入漏洞
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    
    # 使用eval危险函数
    user_input = request.form.get("code")
    result = eval(user_input)
    
    # 不安全的随机数用于安全令牌
    token = random.randint(100000, 999999)
    
    return jsonify({"token": token})`

const performDetection = () => {
  results.value = []
  const lines = code.value.split('\n')
  
  detectionRules.forEach(rule => {
    lines.forEach((line, index) => {
      const match = rule.pattern.exec(line)
      if (match) {
        results.value.push({
          ...rule,
          match_line: line.trim(),
          line_number: index + 1
        })
      }
    })
  })
  
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  results.value.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])
}

const handleAudit = () => {
  if (!code.value.trim()) {
    ElMessage.warning('请输入需要审计的代码')
    return
  }
  
  loading.value = true
  results.value = []
  
  setTimeout(() => {
    performDetection()
    loading.value = false
    
    if (results.value.length === 0) {
      ElMessage.success('未发现明显的安全问题')
    } else {
      ElMessage.warning('发现 ' + results.value.length + ' 个安全问题')
    }
  }, 500)
}

const handleClear = () => {
  code.value = ''
  results.value = []
}

const handleSample = () => {
  language.value = 'auto'
  code.value = sampleCode
  ElMessage.success('已加载Python示例代码')
}

const getSeverityType = (severity) => {
  const types = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return types[severity] || 'info'
}
</script>

<style scoped>
.quick-audit {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.code-input :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
}

.action-bar {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.empty-result {
  padding: 40px 0;
}

.results-container {
  max-height: 600px;
  overflow-y: auto;
}

.result-item {
  margin-bottom: 15px;
}

.issue-card :deep(.el-card__header) {
  padding: 10px 15px;
  background-color: #f5f7fa;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.issue-title {
  font-weight: bold;
  flex: 1;
}

.cwe-link {
  color: #409eff;
  text-decoration: none;
}

.cwe-link:hover {
  text-decoration: underline;
}

.issue-content {
  font-size: 14px;
}

.issue-section {
  margin-bottom: 10px;
}

.issue-section strong {
  color: #606266;
}

.code-snippet {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 5px;
}

.recommendation {
  color: #67c23a;
}
</style>
