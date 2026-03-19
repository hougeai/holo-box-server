#!/bin/bash
# 启动 Celery Worker

# 检查程序是否运行（celery worker 会有多个进程，用 pkill 全部杀掉）
PID=$(ps aux | grep 'celery -A core.celery_app worker' | grep -v grep | awk '{print $2}')

# 如果 PID 存在，则杀掉该进程
if [ ! -z "$PID" ]; then
    echo "Process found. Killing celery worker"
    pkill -f 'celery -A core.celery_app worker'
    echo "Process killed."
else
    echo "No process found running "
fi


MODE=${1:-local}  # local=本地开发机，docker=docker容器
WORKERS=${2:-1}  # 并发任务数，默认为 1
# 参数说明：
# -A core.celery_app: 指定 Celery 应用模块
# --loglevel=info: Celery 框架日志级别
# --concurrency: 并发任务数（默认1），Worker 同时最多运行 1 个任务
# --pool=solo: 使用 solo 线程池
# --hostname=holo-box-worker@%h: Worker 名称
# 设置环境变量，标记 Celery Worker 运行中（用于日志区分）
export CELERY_WORKER_RUNNING=1

if [ "$MODE" = "docker" ]; then
    celery -A core.celery_app worker \
        --loglevel=info \
        --concurrency=$WORKERS \
        --pool=solo \
        --hostname=holo-box-worker@%h
else
    nohup celery -A core.celery_app worker \
        --loglevel=info \
        --concurrency=$WORKERS \
        --pool=solo \
        --hostname=holo-box-worker@%h > data/logs/celery_worker.log 2>&1 &
    echo "Celery Worker started with $WORKERS workers"
fi
