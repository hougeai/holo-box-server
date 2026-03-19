"""
Celery 任务队列配置和任务定义
用于异步视频生成任务
"""

import hashlib
import asyncio
from tortoise import Tortoise
from celery import Celery, shared_task
from celery.signals import task_prerun, worker_shutdown
from core.config import settings
from core.profile_api import bl_service
from core.utils import resize_video_in_memory
from core.minio import oss
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
def generate_videos(self, profile_id: int, img_url: str, subject_type: str, batch_size: int = 2):
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
        # asyncio.run(bl_service.generate_and_save_test(profile_id, img_url, subject_type, batch_size))
        asyncio.run(bl_service.generate_and_save(profile_id, img_url, subject_type, batch_size))
        logger.info(f'视频生成任务完成: profile_id={profile_id}')
    except Exception as e:
        logger.error(f'视频生成任务异常: profile_id={profile_id}, error={e}')
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=2)
def generate_single_video(self, profile_id: int, gen_img: str, subject_type: str, emotion: str):
    """
    异步生成单个形象视频（编辑模式）

    Args:
        profile_id: 形象ID
        gen_img: 生成图片的URL
        subject_type: 主体类型
        emotion: 情感/动作类型
    """

    async def _run():
        # 1. 生成视频
        video_url, msg = await bl_service.generate_video(gen_img, subject_type, emotion=emotion)
        if not video_url:
            raise Exception(f'生成视频失败: {msg}')

        # 2. 下载视频
        video_data, content_type = await bl_service.download_file(video_url, 'video/mp4')

        # 3. 转换视频尺寸
        resized_data = await resize_video_in_memory(video_data)
        if not resized_data:
            raise Exception('视频转换失败')

        # 4. 上传到OSS
        video_key = f'profile/vid/{profile_id}/{emotion}.mp4'
        result = await oss.upload_file_async(video_key, file_data=resized_data, content_type=content_type)
        if not result:
            raise Exception('上传视频失败')

        # 5. 计算hash并返回结果
        final_url = f'{settings.OSS_BUCKET_URL}/{video_key}'
        video_hash = hashlib.sha256(video_data).hexdigest()

        return {'video_url': final_url, 'video_hash': video_hash, 'emotion': emotion}

    try:
        logger.info(f'开始生成单个视频: profile_id={profile_id}, emotion={emotion}')
        result = asyncio.run(_run())
        logger.info(f'单个视频生成完成: profile_id={profile_id}, emotion={emotion}')
        return result
    except Exception as e:
        logger.error(f'单个视频生成失败: profile_id={profile_id}, emotion={emotion}, error={e}')
        raise self.retry(exc=e, countdown=60)
