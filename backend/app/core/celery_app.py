"""
Celery 任务队列配置和任务定义
用于异步视频生成任务
"""

import asyncio
from tortoise import Tortoise
from celery import Celery, shared_task
from celery.signals import task_prerun, worker_shutdown
from core.config import settings
from core.profile_api import bl_service
from core.log import logger

# Redis broker URL (存储待执行的任务-消费队列)
broker_url = f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
# Redis backend URL (存储任务结果-1天过期)
backend_url = f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'

# 创建 Celery 应用
celery_app = Celery(
    'holo_box_tasks',
    broker=broker_url,
    backend=backend_url,
)


# Celery 配置
celery_app.conf.update(
    # 任务序列化方式
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    # 时区设置
    timezone='Asia/Shanghai',
    enable_utc=True,
    # 任务结果过期时间（1天）
    result_expires=86400,
    # 任务状态跟踪：STARTED
    task_track_started=True,  # 任务开始执行时记录STARTED状态
    # 任务限流：每分钟最多执行10个任务
    task_rate_limit='10/m',
    # 任务超时时间：30分钟
    task_soft_time_limit=1800,
    task_time_limit=1800,
    # 任务自动重试配置
    task_acks_late=True,  # 任务执行完才确认
    task_reject_on_worker_lost=True,  # Worker 丢失时拒绝任务
    # Worker 配置
    worker_prefetch_multiplier=1,  # 每个 Worker 每次只预取1个任务
)


# Worker 关闭时断开数据库
@task_prerun.connect
def init_tortoise(**kwargs):
    """任务执行前检查并初始化数据库"""
    try:
        # 尝试获取默认连接，已初始化则通过，未初始化则捕获异常
        Tortoise.get_connection()
    except Exception:
        asyncio.run(Tortoise.init(config=settings.TORTOISE_ORM))


@worker_shutdown.connect
def close_tortoise(**kwargs):
    """Worker 关闭时断开数据库连接"""
    try:
        asyncio.run(Tortoise.close_connections())
    except Exception:
        pass  # 已经关闭或从未初始化，忽略即可


@shared_task(bind=True, max_retries=2)
def generate_video_task(self, profile_id: int, img_url: str, subject_type: str, batch_size: int = 2):
    """
    异步生成形象视频任务

    Args:
        profile_id: 形象ID
        img_url: 生成视频的图片URL
        subject_type: 主体类型（human/animal等）
        batch_size: 批次大小
    """

    try:
        logger.info(f'开始执行视频生成任务: profile_id={profile_id}')
        asyncio.run(bl_service.generate_and_save_test(profile_id, img_url, subject_type, batch_size))
        logger.info(f'视频生成任务完成: profile_id={profile_id}')
    except Exception as e:
        logger.error(f'视频生成任务异常: profile_id={profile_id}, error={e}')
        raise self.retry(exc=e, countdown=60)
