import aiohttp
import asyncio
import hashlib
import io
import json
import os
from PIL import Image
from openai import AsyncOpenAI
from models.agent import Profile
from .config import settings
from .log import logger
from .minio import oss


# 加载 prompt 配置文件
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'profile.json')


def _load_prompts():
    """加载 prompt 配置"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('img_prompt', {}), config.get('vid_prompts', {}), config.get('char_polish_prompt', {})
    except Exception as e:
        logger.error(f'加载 prompt 配置文件失败: {e}')
        return {}, {}


img_prompt, vid_prompts, char_polish_prompt = _load_prompts()


class BailianService:
    def __init__(self):
        self.base_url = 'https://dashscope.aliyuncs.com/api/v1'
        self.headers = {'Authorization': f'Bearer {settings.BAILIAN_KEY}'}

    async def _make_request(self, method, url, headers, **kwargs):
        """通用HTTP请求方法"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, **kwargs) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f'请求百炼失败: {response.status} {error_text}')
                        return None, f'请求百炼失败: {error_text}'
                    data = await response.json()
                    logger.info(f'百炼返回: {data}')
                    return data, 'success'
        except Exception as e:
            logger.error(f'请求失败 [{method} {url}]: {e}')
            return None, f'请求百炼失败: {e}'

    async def download_file(self, url, default_content_type):
        """
        下载文件
        :param url: 文件URL
        :param default_content_type: 默认content_type
        :return: (文件字节数据, content_type)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f'下载文件失败: {response.status}')
                        return None, None
                    # 从响应头获取实际类型
                    content_type = response.headers.get('Content-Type', default_content_type)
                    return await response.read(), content_type
        except Exception as e:
            logger.error(f'下载文件失败: {e}')
            return None, None

    def validate_image_size(self, img_bytes, min_dim=384, max_dim=5000):
        """
        验证图片尺寸是否满足百炼API要求
        :param img_bytes: 图片字节数据
        :param min_dim: 最小边尺寸要求
        :param max_dim: 最大边尺寸要求
        :return: (True, None)表示验证通过，(False, 错误信息)表示验证失败
        """
        try:
            img = Image.open(io.BytesIO(img_bytes))
            width, height = img.size
            min_side = min(width, height)
            max_side = max(width, height)
            # 检查尺寸是否超出最大限制
            if max_side > max_dim:
                return (
                    False,
                    f'图片尺寸过大，最小边不小于{min_dim}px，最大边不超过{max_dim}px，当前图片为{width}x{height}',
                )
            # 检查尺寸是否满足最小要求
            if min_side < min_dim:
                return (
                    False,
                    f'图片尺寸过小，最小边不小于{min_dim}px，最大边不超过{max_dim}px，当前图片为{width}x{height}',
                )
            return True, None

        except Exception as e:
            logger.error(f'验证图片尺寸失败: {e}')
            return False, f'图片格式错误或损坏: {str(e)}'

    async def generate_image(self, img_url, subject_type):
        """
        生成图片
        :param img_url: 图片地址 or base64
        """
        url = f'{self.base_url}/services/aigc/multimodal-generation/generation'
        data = {
            'model': 'wan2.6-image',
            'input': {
                'messages': [{'role': 'user', 'content': [{'text': img_prompt[subject_type]}, {'image': img_url}]}]
            },
            'parameters': {'n': 1, 'size': '720*1440'},
        }
        res, msg = await self._make_request('POST', url, self.headers, json=data)
        if not res:
            return None, msg
        try:
            image = res['output']['choices'][0]['message']['content'][0]['image']
            return image, 'success'
        except Exception as e:
            logger.error(f'百炼返回数据错误: {e}')
            return None, '百炼返回数据错误'

    async def post_generate_video(self, prompt, img_url):
        headers = self.headers.copy()
        headers['X-DashScope-Async'] = 'enable'
        url = f'{self.base_url}/services/aigc/video-generation/video-synthesis'
        # url = f'{self.base_url}/services/aigc/image2video/video-synthesis'
        data = {
            'model': 'wan2.2-i2v-flash',
            'input': {'prompt': prompt, 'img_url': img_url},
            # 'model': 'wan2.2-kf2v-flash',
            # 'input': {'prompt': prompt, 'first_frame_url': img_url, 'last_frame_url': img_url},
            'parameters': {'resolution': '720P', 'duration': 5},
        }
        res, msg = await self._make_request('POST', url, headers, json=data)
        if not res:
            return None, msg
        try:
            task_id = res['output']['task_id']
            task_status = res['output']['task_status']
            return task_id, task_status
        except Exception as e:
            logger.error(f'百炼返回数据错误: {e}')
            return None, '百炼返回数据错误'

    async def get_video_status(self, task_id):
        url = f'{self.base_url}/tasks/{task_id}'
        res, msg = await self._make_request('GET', url, self.headers)
        if not res:
            return None, msg
        try:
            task_status = res['output']['task_status']
            if task_status == 'SUCCEEDED':
                video_url = res['output']['video_url']
                return video_url, task_status
            else:
                return None, task_status
        except Exception as e:
            logger.error(f'百炼返回数据错误: {e}')
            return None, '百炼返回数据错误'

    async def generate_video(self, img_url, subject_type, emotion='normal'):
        """
        生成视频
        :param img_url: 图片地址
        :param emotion: 情绪类型
        """
        vid_prompt = vid_prompts[subject_type]
        prompt = '\n'.join([vid_prompt['background'], vid_prompt['action'].get(emotion, '')])
        # logger.info(f'百炼视频生成: {emotion} {prompt}')
        task_id, task_status = await self.post_generate_video(prompt, img_url)
        if not task_id:
            return None, '百炼视频生成任务创建失败'

        max_retries = 40  # 最大重试次数，最多等待200秒
        retry_count = 0

        # 开始轮询获取结果
        while task_status in ['PENDING', 'RUNNING'] and retry_count < max_retries:
            await asyncio.sleep(5)
            video_url, task_status = await self.get_video_status(task_id)
            logger.info(f'百炼视频生成: {task_id} {task_status} [{retry_count + 1}/{max_retries}]')
            retry_count += 1

        if task_status == 'SUCCEEDED':
            return video_url, 'success'
        else:
            logger.error(f'百炼视频生成超时或失败: {task_id} {task_status}')
            return None, f'百炼视频生成超时或失败: {task_id} {task_status}'

    async def generate_and_save(self, profile_id, img_url, subject_type, batch_size=2):
        try:
            # 获取所有情绪类型
            emotions = list(vid_prompts[subject_type]['action'].keys())
            results = {}
            # 分批处理情绪视频生成任务
            for i in range(0, len(emotions), batch_size):
                batch_emotions = emotions[i : i + batch_size]
                logger.info(f'正在处理情绪批次: {batch_emotions}')

                # 创建当前批次的任务
                batch_tasks = [self.generate_video(img_url, subject_type, emotion) for emotion in batch_emotions]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                # 处理当前批次的结果
                for j, result in enumerate(batch_results):
                    emotion = batch_emotions[j]
                    # 处理可能的异常情况
                    if isinstance(result, Exception):
                        logger.error(f'生成情绪 {emotion} 的视频时发生异常: {result}')
                        results[emotion] = {'url': None, 'status': 'failed', 'msg': str(result)}
                        continue
                    video_url, status = result
                    if status == 'success':
                        results[emotion] = {'url': video_url, 'status': 'success', 'msg': ''}
                    else:
                        results[emotion] = {'url': None, 'status': 'failed', 'msg': status}
                # 在批次之间增加延迟以减少API压力
                if i + batch_size < len(emotions):
                    await asyncio.sleep(1)
            # 保存结果到数据库
            profile = await Profile.get(id=profile_id)

            # 下载视频并上传到 OSS
            for emotion, info in results.items():
                if info['status'] == 'success' and info['url']:
                    suffix = hashlib.sha256(f'{profile_id}-{emotion}'.encode()).hexdigest()[:4]
                    video_key = f'profile/vid/{profile_id}-{emotion}-{suffix}.mp4'
                    video_data, content_type = await self.download_file(info['url'], 'video/mp4')
                    if video_data:
                        upload_result = await oss.upload_file_async(
                            video_key, file_data=video_data, content_type=content_type
                        )
                        if upload_result:
                            info['url'] = f'{settings.OSS_BUCKET_URL}/{video_key}'
                            info['hash'] = hashlib.sha256(video_data).hexdigest()
                        else:
                            logger.error(f'视频上传失败: {emotion}')
                            info['url'] = ''
                            info['hash'] = ''
                            info['status'] = 'failed'
                            info['msg'] = '上传到OSS失败'
            profile.gen_vids = results
            profile.status = 'success'
            await profile.save()
            logger.info(f'{profile_id} 百炼视频生成结果已保存')
            return results
        except Exception as e:
            logger.error(f'{profile_id} 百炼视频生成结果保存失败: {e}')
            # 如果出现异常，仍然尝试更新数据库状态
            try:
                profile = await Profile.get(id=profile_id)
                profile.status = 'failed'
                await profile.save()
            except Exception as db_e:
                logger.error(f'更新数据库状态失败: {db_e}')
            raise e


bl_service = BailianService()


class LLM:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.BAILIAN_KEY, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
        )
        self.model = 'qwen-flash'

    async def __call__(self, content, temperature=0.7):
        try:
            messages = [
                {'role': 'system', 'content': char_polish_prompt},
                {'role': 'user', 'content': content},
            ]
            completion = await self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, stream=False
            )
            return completion.choices[-1].message.content
        except Exception as e:
            logger.error(f'LLM error: {e}')
            return ''


llm = LLM()
