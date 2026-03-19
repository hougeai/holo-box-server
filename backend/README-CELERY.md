# Celery 视频生成任务系统使用说明

## 架构说明

使用 Celery + Redis 实现异步视频生成任务：
- **Celery**: 分布式任务队列框架
- **Redis**: 作为 broker（任务队列）和 backend（结果存储）
- **FastAPI**: 提交任务到队列
- **Celery Worker**: 独立进程执行任务

## 安装依赖

```bash
cd backend
uv add celery
```

## 启动方式

### 1. 启动 Redis

```bash
# Docker 启动
docker run -d -p 6379:6379 redis:7

# 或者使用系统服务
sudo systemctl start redis
```

### 2. 启动 Celery Worker（必需）

**方案一：同机部署（推荐开发环境）**

```bash
cd backend/app
bash start_celery.sh
```

**方案二：手动启动**

```bash
cd backend/app
celery -A core.celery_app worker --loglevel=info --concurrency=2 --pool=solo
```

**方案三：独立机器部署（推荐生产环境）**

在另一台服务器上运行 Worker，配置相同的 Redis 连接即可。

**参数说明：**
- `-A core.celery_app`: 指定 Celery 应用模块
- `--loglevel=info`: 日志级别
- `--concurrency=2`: 并发任务数（根据服务器性能调整）
- `--pool=solo`: 使用 solo 池（适用于异步任务）


## 任务状态查询

任务状态存储在 Redis 中，可通过 Celery API 查询：

```python
from core.celery_app import celery_app
from celery.result import AsyncResult

# 提交任务并获取 task_id
task = generate_video_task.delay(profile_id, img_url, subject_type, batch_size)
task_id = task.id

# 查询任务状态
result = AsyncResult(task_id, app=celery_app)
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
print(result.result)  # 任务结果或异常信息
```

**状态说明：**
- `PENDING`: 任务等待执行
- `STARTED`: 任务正在执行
- `SUCCESS`: 任务执行成功
- `FAILURE`: 任务执行失败
- `RETRY`: 任务正在重试

## 数据库状态

任务状态同步到 `Profile` 表的 `status` 字段：
- `processing`: 任务提交后立即设置
- `success`: 所有视频生成成功
- `failed`: 任务执行失败

前端通过查询 `Profile` 接口获取任务状态。

## 任务失败重试

Celery 配置了自动重试：
- 最大重试次数：3次
- 重试间隔：60秒

## 监控

### 1. Celery Flower（可选）

```bash
pip install flower
celery -A core.celery_app flower --port=5555
```

访问 http://localhost:5555 查看任务监控界面。

### 2. 日志

Worker 日志输出到控制台，可重定向到文件：

```bash
bash start_celery_worker.sh >> celery_worker.log 2>&1
```

## 部署建议

### 开发环境
- FastAPI 和 Celery Worker 同机部署
- 并发数：2

### 生产环境
- Celery Worker 独立部署（可多台）
- 并发数：根据服务器性能调整（建议4-8）
- 使用 supervisor 或 systemd 管理 Worker 进程

## 故障处理

1. **Worker 挂掉**
   - 任务会重新分配给其他 Worker
   - 使用 `--autoreload` 可在代码变更时自动重启

2. **Redis 连接失败**
   - 检查 Redis 是否启动
   - 检查防火墙配置

3. **任务堆积**
   - 增加并发数 `--concurrency`
   - 增加机器数量
