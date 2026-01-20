import aiohttp
import asyncio
from .config import settings
from .log import logger


img_prompt = """
**核心指令：** 基于给定参考图，生成一张该人物的**正面全身肖像照**，要求人物在画面中**完整可见（从头到脚）**，人物高度在图片中占满95%，正常站立姿势，背景为**纯黑色**，地面为黑色，营造**干净、专业的工作室氛围**。

**人物细节：**
- **相貌与神态：** 严格保持与参考图像一致的相貌特征。面部神态**自然、放松**，带有**微妙的浅笑**，展现亲和力。
- **服装与造型：** 精确还原参考图的上身服装样式。基于此风格，**合理推理并生成协调搭配的下半身服装与鞋子**，不要携带任何配件比如包不包等，确保整体造型风格统一、真实可信。
- **画面质感：** **电影级画质**，**超真实感**，突出人物轮廓与质感，细节锐利。分辨率高，人物主体清晰。

**关键修饰词：** full body portrait, head to toe, clean black background, professional photography, cinematic, hyperrealistic, photorealistic, 8k, detailed eyes and face, subtle smile.
"""

vid_prompts = {
    'normal': '全景镜头，人物全身（占画面90%），纯黑色背景没有任何杂物和干扰光源，面带微笑，自然站立微微地晃动身体，固定机位360度旋转，电影感画质。',
    'happy': '全景镜头，人物全身（占画面90%），固定镜头，纯黑色背景没有任何杂物和干扰光源，电影感画质。人物嘴角微微上扬，面部肌肉放松，嘴里说着些话，好像是在谆谆教诲的感觉。',
}


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
                        logger.error(f'请求百炼失败: {response.status} {response.text}')
                        return None, f'请求百炼失败: {response.status}'
                    data = await response.json()
                    logger.info(f'百炼返回: {data}')
                    return data, 'success'
        except Exception as e:
            logger.error(f'请求失败 [{method} {url}]: {e}')
            return None, f'请求百炼失败: {e}'

    async def generate_image(self, img_url):
        """
        生成图片
        :param img_url: 图片地址
        """
        url = f'{self.base_url}/services/aigc/multimodal-generation/generation'
        data = {
            'model': 'wan2.6-image',
            'input': {'messages': [{'role': 'user', 'content': [{'text': img_prompt}, {'image': img_url}]}]},
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
        data = {
            'model': 'wan2.2-i2v-flash',
            'input': {'prompt': prompt, 'img_url': img_url},
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

    async def generate_video(self, img_url, emotion='normal'):
        """
        生成视频
        :param img_url: 图片地址
        """
        prompt = vid_prompts.get(emotion, '')
        task_id, task_status = await self.post_generate_video(prompt, img_url)
        if not task_id:
            return None, '百炼视频生成任务创建失败'
        # 开始轮询获取结果
        while task_status in ['PENDING', 'RUNNING']:
            await asyncio.sleep(5)
            video_url, task_status = await self.get_video_status(task_id)
            logger.info(f'百炼视频生成: {task_id} {task_status}')
        if task_status == 'SUCCEEDED':
            return video_url, 'success'
        else:
            return None, '百炼视频生成失败'


bl_service = BailianService()
