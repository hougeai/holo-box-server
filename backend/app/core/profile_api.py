import aiohttp
import asyncio
from models.agent import Profile
from .config import settings
from .log import logger
from .minio import oss


img_prompt = """
**核心指令：** 基于给定参考图，生成一张该人物的**正面全身肖像照**，要求人物在画面中**完整可见（从头到脚）**，人物高度在图片中占满95%，正常站立姿势，背景为**纯黑色**，地面为黑色，营造**干净、专业的工作室氛围**。

**人物细节：**
- **相貌与神态：** 严格保持与参考图像一致的相貌特征。面部神态**自然、放松**，带有**微妙的浅笑**，展现亲和力。
- **服装与造型：** 精确还原参考图的上身服装样式。基于此风格，**合理推理并生成协调搭配的下半身服装与鞋子**，不要携带任何配件比如包不包等，确保整体造型风格统一、真实可信。
- **画面质感：** **电影级画质**，**超真实感**，突出人物轮廓与质感，细节锐利。分辨率高，人物主体清晰。

**关键修饰词：** full body portrait, head to toe, clean black background, professional photography, cinematic, hyperrealistic, photorealistic, 8k, detailed eyes and face, subtle smile.
"""

VID_PREFIX = '全景镜头，人物全身（占画面90%），固定镜头，纯黑色背景没有任何杂物和干扰光源，电影感画质。'

VID_SUFFIX = {
    'happy': '人物嘴角微微上扬，面部肌肉放松，嘴里说着些话，好像是在谆谆教诲的感觉。',
    'sad': '人物眉头微蹙，眼神忧郁，嘴角下垂，神情悲伤，身体微微低垂，整个人散发出失落和难过的心情。',
    'angry': '人物眉头紧锁，眼神锐利且带着怒意，嘴角紧抿，面部肌肉紧绷，神情愤怒，身体略微前倾，散发出不容置疑的威严和怒火。',
    'love': '人物眼神温柔而深情，嘴角含着甜蜜的微笑，面部表情柔和，身体姿态放松，仿佛在向最爱的人表达爱意，充满温暖和爱恋的氛围。',
    'surprised': '人物眼睛微微睁大，眉毛上扬，嘴巴微张，神情中带着惊讶和意外，身体略向后倾，反应自然而生动。',
    'shocked': '人物双眼大睁，瞳孔放大，眉毛高高扬起，嘴巴张开，神情中充满震惊和难以置信，身体僵硬，表现出强烈的意外感。',
    'neutral': '面带微笑，自然站立微微地晃动身体，固定机位360度旋转。',
    'calm': '人物神情平和，眼神安静，嘴角保持轻微的微笑，表情淡然，身体姿态自然放松，散发出宁静祥和的气质。',
    'playful': '人物眼神灵动活泼，嘴角带着顽皮的笑意，眉毛微微上挑，身体轻快地晃动，整个人散发出开心俏皮、活泼可爱的氛围。',
    'embarrassed': '人物脸颊泛红，眼神有些躲闪，嘴角尴尬地抽动，眉毛微微皱起，身体略显僵硬，表现出害羞和局促不安的样子。',
}

vid_prompts = {k: VID_PREFIX + v for k, v in VID_SUFFIX.items()}


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

    async def generate_image(self, img_url):
        """
        生成图片
        :param img_url: 图片地址 or base64
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
        :param emotion: 情绪类型
        """
        prompt = vid_prompts.get(emotion, '')
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

    async def generate_and_save(self, profile_id, img_url, batch_size=2):
        try:
            # 获取所有情绪类型
            emotions = list(vid_prompts.keys())
            results = {}
            # 分批处理情绪视频生成任务
            for i in range(0, len(emotions), batch_size):
                batch_emotions = emotions[i : i + batch_size]
                logger.info(f'正在处理情绪批次: {batch_emotions}')

                # 创建当前批次的任务
                batch_tasks = [self.generate_video(img_url, emotion) for emotion in batch_emotions]
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
                    video_key = f'profile/vid/{profile_id}-{emotion}.mp4'
                    video_data, content_type = await self.download_file(info['url'], 'video/mp4')
                    if video_data:
                        upload_result = await oss.upload_file_async(
                            video_key, file_data=video_data, content_type=content_type
                        )
                        if upload_result:
                            info['url'] = f'{settings.OSS_BUCKET_URL}/{video_key}'
                        else:
                            logger.error(f'视频上传失败: {emotion}')
                            info['url'] = None
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

    # 以下函数废弃：并发限制为2不能这么做
    async def submit_all_emotions(self, img_url):
        """
        提交生成所有情绪的视频任务
        :param img_url: 图片地址
        :return: {emotion: {'task_id': task_id, 'status': 'success'|'failed'}}
        """
        submit_tasks = [self.post_generate_video(vid_prompts[e], img_url) for e in vid_prompts.keys()]
        task_list = await asyncio.gather(*submit_tasks)
        # 收集任务ID
        pending = {}
        for idx, (task_id, task_status) in enumerate(task_list):
            emotion = list(vid_prompts.keys())[idx]
            if task_id:
                pending[emotion] = {'task_id': task_id, 'status': task_status, 'retries': 0}
        return pending

    async def poll_all_emotions(self, pending):
        """
        后台任务：轮询视频生成状态
        """
        results = {}
        max_retries = 40
        # 轮询直到所有任务完成或超时
        while pending:
            await asyncio.sleep(5)
            # 批量查询状态
            status_tasks = [self.get_video_status(v['task_id']) for v in pending.values()]
            status_results = await asyncio.gather(*status_tasks)

            for (emotion, info), (video_url, task_status) in zip(pending.items(), status_results):
                info['retries'] += 1
                logger.info(f'情绪 {emotion}: {info["task_id"]} {task_status} [{info["retries"]}/{max_retries}]')
                if task_status == 'SUCCEEDED':
                    results[emotion] = {'url': video_url, 'status': 'success', 'msg': ''}
                elif task_status not in ['PENDING', 'RUNNING'] or info['retries'] >= max_retries:
                    results[emotion] = {'url': None, 'status': 'failed', 'msg': task_status}
            # 移除已完成的任务
            pending = {k: v for k, v in pending.items() if k not in results}
        return results

    async def poll_and_save(self, pending, profile_id):
        try:
            results = await self.poll_all_emotions(pending)
            profile = await Profile.get(id=profile_id)

            # 下载视频并上传到 OSS
            for emotion, info in results.items():
                if info['status'] == 'success' and info['url']:
                    video_key = f'profile/vid/{profile_id}-{emotion}.mp4'
                    video_data, content_type = await self.download_file(info['url'], 'video/mp4')
                    if video_data:
                        upload_result = await oss.upload_file_async(
                            video_key, file_data=video_data, content_type=content_type
                        )
                        if upload_result:
                            # 更新为 OSS URL
                            info['url'] = f'{settings.OSS_BUCKET_URL}/{video_key}'
                        else:
                            logger.error(f'视频上传失败: {emotion}')
                            info['status'] = 'failed'
                            info['msg'] = '上传到OSS失败'
            profile.gen_vids = results
            profile.status = 'success'
            await profile.save()
            logger.info(f'{profile_id} 百炼视频生成结果已保存')
        except Exception as e:
            logger.error(f'{profile_id} 百炼视频生成结果保存失败: {e}')


bl_service = BailianService()
