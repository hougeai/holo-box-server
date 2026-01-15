import aiohttp
from .config import settings
from .log import logger


class XZService:
    def __init__(self):
        self.base_url = settings.XZ_API_URL
        self.headers = {'Authorization': 'Bearer'}

    async def _make_request(self, method, url, **kwargs):
        """通用HTTP请求方法"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=self.headers, **kwargs) as response:
                    if response.status != 200:
                        logger.error(f'请求失败 [{method} {url}]: {response.status}')
                        return None
                    data = await response.json()
                    return data
        except Exception as e:
            logger.error(f'请求失败 [{method} {url}]: {e}')
            return None

    async def list_agent(self):
        """智能体列表"""
        url = f'{self.base_url}/xiaozhi/agent/list'
        return await self._make_request('GET', url)

    async def create_agent(self, name):
        """创建智能体"""
        data = {'agentName': name}
        url = f'{self.base_url}/xiaozhi/agent'
        return await self._make_request('POST', url, json=data)

    async def update_agent(self, id, obj):
        """更新智能体"""
        data = {}
        if obj.agent_name:
            data['agentName'] = obj.agent_name
        if obj.llm_model_id:
            data['llmModelId'] = obj.llm_model_id
        if obj.tts_voice_id:
            data['ttsVoiceId'] = obj.tts_voice_id
        if obj.system_prompt:
            data['systemPrompt'] = obj.system_prompt
        url = f'{self.base_url}/xiaozhi/agent/{id}'
        return await self._make_request('PUT', url, json=data)

    async def delete_agent(self, id):
        """删除智能体"""
        url = f'{self.base_url}/xiaozhi/agent/{id}'
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

    async def list_llm(self):
        """LLM模型列表"""
        url = f'{self.base_url}/v1/agents/models/llm'
        return await self._make_request('GET', url)

    async def list_voice(self):
        """TTS语音列表"""
        url = f'{self.base_url}/v1/voices'
        return await self._make_request('GET', url)

    async def create_voice(self):
        """创建音色栏位"""
        url = f'{self.base_url}/v1/voice-clones'
        return await self._make_request('POST', url, json={'model_id': 'QN_ACV'})

    async def clone_voice(self, id, ref_audio, name):
        """克隆音色"""
        url = f'{self.base_url}/v1/voice-clones/{id}'
        return await self._make_request('PUT', url, json={'key': ref_audio, 'name': name})

    async def get_voice(self, id):
        """获取音色"""
        url = f'{self.base_url}/v1/voice-clones/{id}'
        return await self._make_request('GET', url)

    async def delete_voice(self, id):
        """删除音色"""
        url = f'{self.base_url}/v1/voice-clones/{id}'
        return await self._make_request('DELETE', url)


xz_service = XZService()
