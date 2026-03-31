# DeepAudit Lite - 安全审计系统

本地优先的安全审计平台，支持离线特征匹配和在线AI增强分析。

## 功能特性

- **代码审计**：支持AI分析和特征匹配，检测SQL注入、硬编码密钥等漏洞
- **日志审计**：导入日志文件，AI识别攻击链条
- **流量分析**：解析PCAP文件，生成攻击链路图
- **自定义规则**：YAML格式规则，灵活扩展检测能力
- **报告生成**：导出Markdown/PDF格式审计报告

## 技术栈

- **后端**：Python 3.10+ / FastAPI / SQLAlchemy / Celery
- **前端**：Vue 3 / Element Plus / ECharts
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **AI**：支持 OpenAI、Ollama、智谱AI 等

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose（可选）

### 使用 Docker 启动

```bash
# 克隆项目
git clone <repository-url>
cd deepaudit-lite

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 填入你的 AI API Key

# 启动所有服务
docker-compose up -d
```

访问 http://localhost:3000

### 本地开发启动

**后端：**

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```bash
cd frontend

# 安装依赖
npm install

# 启动服务
npm run dev
```

## 配置说明

### AI 配置

在 `backend/.env` 中配置：

```env
AI_PROVIDER=openai          # openai / ollama / zhipu
AI_API_KEY=your-api-key    # API密钥
AI_BASE_URL=https://api.openai.com/v1  # API地址
AI_MODEL=gpt-4            # 模型名称
```

### 使用本地 Ollama

```env
AI_PROVIDER=ollama
AI_BASE_URL=http://localhost:11434
AI_MODEL=llama3
```

## 项目结构

```
deepaudit-lite/
├── backend/
│   ├── app/
│   │   ├── api/          # API接口
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic模型
│   │   ├── services/     # 业务逻辑
│   │   ├── tasks/        # Celery任务
│   │   └── utils/        # 工具函数
│   ├── uploads/          # 上传文件目录
│   ├── reports/          # 报告目录
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # API调用
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面视图
│   │   ├── router/       # 路由
│   │   └── store/        # 状态管理
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API 接口

### 审计任务

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/audit/upload | 上传文件创建任务 |
| GET | /api/audit/tasks | 获取任务列表 |
| GET | /api/audit/tasks/{id} | 获取任务详情 |
| DELETE | /api/audit/tasks/{id} | 删除任务 |
| GET | /api/audit/statistics | 获取统计信息 |

### 规则管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/rules | 获取规则列表 |
| POST | /api/rules | 创建规则 |
| PUT | /api/rules/{id} | 更新规则 |
| DELETE | /api/rules/{id} | 删除规则 |

### 报告

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/reports/{task_id}?format=md | 下载Markdown报告 |
| GET | /api/reports/{task_id}?format=pdf | 下载PDF报告 |

## 自定义规则

规则采用YAML格式，示例：

```yaml
id: SQLI-001
name: SQL注入检测
severity: high
language: python
pattern: '(?i)(cursor\.execute|executemany)\s*\([^)]*%s'
message: 检测到使用%s占位的SQL查询，请使用参数化查询
```

## 许可证

MIT License
