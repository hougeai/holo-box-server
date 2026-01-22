import aiohttp
import asyncio
import json
from .config import settings
from .log import logger


class WXService:
    def __init__(self):
        self.base_url = 'https://api.weixin.qq.com'
        self.access_token = None

    async def _make_request(self, method, url, **kwargs):
        """通用HTTP请求方法"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status != 200:
                        logger.error(f'请求微信服务器失败: {response.status}')
                        return None, f'请求微信服务器失败: {response.status}'
                    response_text = await response.text()
                    try:
                        data = json.loads(response_text)
                        logger.info(f'微信服务器返回: {data}')
                    except json.JSONDecodeError:
                        logger.error(f'微信服务器返回非JSON格式: {response_text}')
                        return None, '微信服务器返回非JSON格式'
                    return data, 'success'
        except Exception as e:
            logger.error(f'请求失败 [{method} {url}]: {e}')
            return None, f'请求微信服务器失败: {e}'

    async def get_openid(self, code):
        """获取openid"""
        params = {
            'appid': settings.MP_APPID,
            'secret': settings.MP_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code',
        }
        url = f'{self.base_url}/sns/jscode2session'
        res, msg = await self._make_request('GET', url, params=params)
        if not res:
            return None, msg
        if not res.get('openid'):
            logger.error(f'获取openid失败: {res}')
            return None, res.get('errmsg')
        return res, 'success'

    async def init_access_token(self):
        """初始化access_token"""
        max_attempts = 3
        for _ in range(max_attempts):
            self.access_token = await self.get_access_token()
            if self.access_token:
                break
            await asyncio.sleep(1)

    async def get_access_token(self):
        url = f'{self.base_url}/cgi-bin/stable_token'
        data = {
            'appid': settings.MP_APPID,
            'secret': settings.MP_SECRET,
            'grant_type': 'client_credential',
        }
        res, _ = await self._make_request('POST', url, json=data)
        access_token = res.get('access_token') if res else None
        return access_token

    async def get_phone(self, code):
        """获取手机号"""
        if not self.access_token:
            await self.init_access_token()
        url = f'{self.base_url}/wxa/business/getuserphonenumber?access_token={self.access_token}'
        data = {
            'code': code,
        }
        res, msg = await self._make_request('POST', url, json=data)
        if not res:
            return None, msg

        if res.get('errcode') == 0:
            return res, 'success'
        else:
            if res.get('errcode') in [42001, 40001, 40014, 41001]:
                logger.warning('access_token失效，重新初始化并重试')
                await self.init_access_token()
                url = f'{self.base_url}/wxa/business/getuserphonenumber?access_token={self.access_token}'
                res, msg = await self._make_request('POST', url, json=data)
                if res and res.get('errcode') == 0:
                    return res, 'success'
            logger.error(f'获取手机号失败: {res}')
            return None, res.get('errmsg')


wx_service = WXService()
