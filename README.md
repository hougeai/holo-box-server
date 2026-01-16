# 0. 项目简介

本项目是Holo-Box项目的服务端代码。项目采用前后端分离架构，包含后端服务、管理后台。

## 1. 项目结构

```
holo-box-server/
├── backend/         # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── main.py  # 主应用入口
│   │   ├── api/     # API 路由
│   │   ├── controllers/ # 控制器
│   │   ├── core/    # 核心功能模块
│   │   └── models/  # 数据模型
│   └── pyproject.toml # 依赖配置
├── frontend-admin/  # 前端管理后台 (Vue 3)
├── deploy/          # 部署配置
└── README.md
```

## 2. 技术栈

### 后端 (backend/)
- **框架**: FastAPI (Python)
- **数据库**: Tortoise ORM (支持 SQLite, MySQL, PostgreSQL)
- **异步处理**: asyncio
- **缓存**: Redis
- **Web 服务器**: Uvicorn
- **依赖管理**: uv + pyproject.toml

### 管理后台 (frontend-admin/)
- **框架**: Vue 3 + Vite
- **UI 组件**: Naive UI
- **图表**: ECharts
- **样式**: UnoCSS


## 3. 环境配置

### 3.1 后端配置

1. **Python 环境准备**:
```bash
# 安装 uv (推荐的 Python 包管理器)
pip install uv

# 创建项目环境
uv sync

# 激活环境
source .venv/bin/activate
```

2. **环境变量配置**:
参考 `backend/app/.env.example` 设置环境变量。

### 3.2 前端配置

1. **安装依赖**:
```bash
cd ../frontend-admin
pnpm install
```

## 4. 运行项目

### 4.1 本地开发

1. **启动后端服务**:
```bash
cd backend
source .venv/bin/activate  # 激活 Python 环境
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

2. **启动前端开发服务器**:
```bash

# 管理后台
cd frontend-admin
pnpm dev
```

### 4.2 Docker 部署

项目提供 Docker Compose 配置:

```bash
cd docker
docker-compose up -d
```

服务将运行在:
- 前端: http://localhost:8077
- 后端: http://localhost:3000

## 5. 开发规范

统一用 pre-commit，代码提交前检查。

```
# 安装 pre-commit：
pip install pre-commit
# or
sudo apt install pipx
pipx install pre-commit
# 安装 Git 钩子
pre-commit install
```

### 5.1 Python 代码规范

- 使用 Ruff 进行代码格式化和检查
- 遵循 PEP 8 编码规范
- 使用类型注解

### 5.2 JavaScript/TypeScript 规范

- 使用 ESLint + Prettier
- 组件命名采用 PascalCase

### 5.3 API 设计规范

- 遵循 RESTful API 设计原则
- 使用 JWT 进行身份认证
- 响应格式统一为 JSON


## 6. 部署

1. 构建前端项目:
```bash
cd frontend-admin
pnpm build
```

2. 部署后端:
```bash
cd backend
# 部署到生产环境
uvicorn app.main:app --host 0.0.0.0 --port 3002
```

## 7. 重要配置

### 7.1 数据库配置

项目支持多种数据库，通过 `DB_TYPE` 环境变量切换:
- `sqlite` (默认): 适合开发环境
- `postgres`: 需要安装 `tortoise-orm[asyncpg]`

### 7.2 支付系统

项目集成了微信支付功能，需要配置相关密钥和回调地址。

### 7.3 对象存储

支持阿里云 OSS / MinIO 等多种对象存储服务，用于文件上传和存储。

## 8. 安全注意事项

- 生产环境中必须设置强密码和密钥
- JWT 密钥需要定期更换
- API 端点需要适当的访问控制
- 敏感信息不应硬编码在代码中