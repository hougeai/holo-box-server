import aiohttp
import asyncio
from .config import settings
from .log import logger


class XZService:
    def __init__(self):
        self.base_url = settings.XZ_API_URL
        self.headers = {'Authorization': f'Bearer {settings.XZ_TOKEN}'}

    async def init_headers(self):
        for i in range(5):
            res = await self._get_token()
            if res:
                return
            await asyncio.sleep(1)
            logger.error(f'获取XZ API TOKEN失败，正在重试 {i+1}...')
        raise Exception('获取XZ API TOKEN失败，多次重试后无法完成初始化')

    async def _make_request(self, method, url, **kwargs):
        """通用HTTP请求方法"""
        max_retries = 2  # token失效时最多重试1次
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, headers=self.headers, **kwargs) as response:
                        if response.status == 401:
                            data = await response.json()
                            if data.get('message') == 'Invalid token':
                                logger.warning('Token失效，正在重新获取...')
                                await self.init_headers()
                                if attempt < max_retries - 1:
                                    continue  # 重新发起请求
                        if response.status != 200:
                            logger.error(f'请求失败 [{method} {url}]: {response.status}')
                            return None
                        data = await response.json()
                        logger.info(f'请求成功 [{method} {url}]: {data}')
                        return data
            except Exception as e:
                logger.error(f'请求失败 [{method} {url}]: {e}')
                return None
        return None

    async def _get_token(self):
        url = f'{self.base_url}/api/developers/token'
        res = await self._make_request('POST', url, json={'secret_key': settings.XZ_API_KEY})
        if res.get('data', {}).get('token'):
            self.headers['Authorization'] = f'Bearer {res["data"]["token"]}'
            return True
        return False

    async def list_agent(self):
        """获取所有智能体列表"""
        url = f'{self.base_url}/api/agents'
        results = []
        page = 1
        page_size = 100
        while True:
            params = {'page': page, 'pageSize': page_size}
            data = await self._make_request('GET', url, params=params)
            if not data:
                break
            agents = data.get('data', [])
            if agents:
                results.extend(agents)
            pagination = data.get('pagination', {})
            has_more = pagination.get('hasMore', False)
            if not has_more:
                break
            page += 1
        return results

    async def get_agent(self, id):
        """获取智能体详情"""
        url = f'{self.base_url}/api/agents/{id}'
        return await self._make_request('GET', url)

    async def create_agent(self, obj_in):
        """创建智能体"""
        data = {}
        if obj_in.agent_name:
            data['agent_name'] = obj_in.agent_name
        if obj_in.assistant_name:
            data['assistant_name'] = obj_in.assistant_name
        if obj_in.llm_model:
            data['llm_model'] = obj_in.llm_model
        if obj_in.tts_voice:
            data['tts_voice'] = obj_in.tts_voice
        if obj_in.tts_speech_speed:
            data['tts_speech_speed'] = obj_in.tts_speech_speed  # 角色语速 slow normal fast
        if obj_in.tts_pitch is not None:
            data['tts_pitch'] = obj_in.tts_pitch  # 音高
        if obj_in.asr_speed:
            data['asr_speed'] = obj_in.asr_speed  # 语音识别速度 slow normal fast
        if obj_in.language:
            data['language'] = obj_in.language
        if obj_in.character:
            data['character'] = obj_in.character
        if obj_in.memory_type:
            data['memory_type'] = obj_in.memory_type  # "OFF"、"SHORT_TERM"
        url = f'{self.base_url}/api/agents'
        return await self._make_request('POST', url, json=data)

    async def update_agent(self, id, obj_in):
        """更新智能体"""
        data = {}
        if obj_in.agent_name:
            data['agent_name'] = obj_in.agent_name
        if obj_in.assistant_name:
            data['assistant_name'] = obj_in.assistant_name
        if obj_in.llm_model:
            data['llm_model'] = obj_in.llm_model
        if obj_in.tts_voice:
            data['tts_voice'] = obj_in.tts_voice
        if obj_in.tts_speech_speed:
            data['tts_speech_speed'] = obj_in.tts_speech_speed  # 角色语速 slow normal fast
        if obj_in.tts_pitch is not None:
            data['tts_pitch'] = obj_in.tts_pitch  # 音高
        if obj_in.asr_speed:
            data['asr_speed'] = obj_in.asr_speed  # 语音识别速度 slow normal fast
        if obj_in.language:
            data['language'] = obj_in.language
        if obj_in.character:
            data['character'] = obj_in.character
        if obj_in.memory:
            data['memory'] = obj_in.memory
        if obj_in.memory_type:
            data['memory_type'] = obj_in.memory_type  # "OFF"、"SHORT_TERM"
        if obj_in.mcp_endpoints:
            data['mcp_endpoints'] = obj_in.mcp_endpoints  # 查看 官方MCP 工具接口
        url = f'{self.base_url}/api/agents/{id}/config'
        return await self._make_request('POST', url, json=data)

    async def delete_agent(self, id):
        """删除智能体"""
        url = f'{self.base_url}/api/agents/delete'
        data = {'id': id}
        return await self._make_request('POST', url, json=data)

    # async def get_mcp_list(self):
    #     """获取MCP列表"""
    #     url = f'{self.base_url}/api/agents/common-mcp-tool/list'
    #     data = await self._make_request('GET', url)
    #     if not data:
    #         return None
    #     return data.get('data', [])

    async def list_llm(self):
        """LLM模型列表"""
        url = f'{self.base_url}/api/roles/model-list'
        data = await self._make_request('GET', url)
        if not data:
            return None
        modelList = data.get('data', {}).get('modelList', [])
        return modelList

    async def list_tts(self):
        """TTS语音列表"""
        url = f'{self.base_url}/api/user/tts-list'
        data = await self._make_request('GET', url)
        results = []
        if data:
            tts_voices = data.get('data', {}).get('tts_voices', {})
            for lang, tts_List in tts_voices.items():
                for tts_voice in tts_List:
                    tts_voice['lang'] = lang
                    results.append(tts_voice)
        return results

    async def list_agent_template(self):
        """获取所有智能体模板列表"""
        url = f'{self.base_url}/api/developers/agent-templates/list'
        params = {'page': 1, 'pageSize': 100}
        data = await self._make_request('GET', url, params=params)
        if not data:
            return None
        agents = data.get('data', {}).get('list', [])
        return agents

    async def create_agent_template(self, obj_in):
        """获取智能体模板详情"""
        url = f'{self.base_url}/api/developers/agent-templates-config'
        data = {
            'agent_name': obj_in.agent_name,
            'character': obj_in.character,
            'assistant_name': obj_in.assistant_name,
            'user_name': obj_in.user_name,
            'tts_voices': [f'{obj_in.language}:{obj_in.tts_voice}'],
            'llm_model': obj_in.llm_model,
            'languages': [obj_in.language],
            'tts_speech_speed': obj_in.tts_speech_speed,
            'asr_speed': obj_in.asr_speed,
            'tts_pitch': obj_in.tts_pitch,
            'default_tts_voice': f'{obj_in.language}:{obj_in.tts_voice}',
        }
        return await self._make_request('POST', url, json=data)

    async def update_agent_template(self, id, obj_in):
        """更新智能体模板"""
        url = f'{self.base_url}/api/developers/agent-templates-config/{id}'
        data = {
            'id': id,
            # 'developer_id': obj_in.developer_id,
            'agent_name': obj_in.agent_name,
            'character': obj_in.character,
            'assistant_name': obj_in.assistant_name,
            'user_name': obj_in.user_name,
            'tts_voices': [f'{obj_in.language}:{obj_in.tts_voice}'],
            'llm_model': obj_in.llm_model,
            'languages': [obj_in.language],
            'tts_speech_speed': obj_in.tts_speech_speed,
            'asr_speed': obj_in.asr_speed,
            'tts_pitch': obj_in.tts_pitch,
            'default_tts_voice': f'{obj_in.language}:{obj_in.tts_voice}',
        }
        return await self._make_request('PUT', url, json=data)

    async def delete_agent_template(self, id):
        """删除智能体模板"""
        url = f'{self.base_url}/api/developers/agent-templates/{id}'
        return await self._make_request('DELETE', url)

    async def bind_device(self, agentId, deviceCode):
        """绑定设备"""
        url = f'{self.base_url}/xiaozhi/device/bind/{agentId}/{deviceCode}'
        return await self._make_request('POST', url)

    async def unbind_device(self, deviceId):
        """解绑设备"""
        data = {'deviceId': deviceId}
        url = f'{self.base_url}/xiaozhi/device/unbind'
        return await self._make_request('POST', url, json=data)

    async def list_device(self, agentId):
        """设备列表"""
        url = f'{self.base_url}/xiaozhi/device/bind/{agentId}'
        return await self._make_request('GET', url)


xz_service = XZService()
