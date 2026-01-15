import aiohttp
from .config import settings
from .log import logger
from .redis_client import get_cache, set_cache


class IP2Location:
    def __init__(self):
        self.gd_key = settings.GD_KEY
        self.bd_key = settings.BD_KEY
        self.hz_id = settings.HZ_ID
        self.hz_key = settings.HZ_KEY
        self.bd_url = 'http://api.map.baidu.com/location/ip'
        self.gd_url = 'https://restapi.amap.com/v3/ip'
        self.hz1_url = 'https://cn.apihz.cn/api/ip/ipbaidu.php'
        self.hz2_url = 'https://cn.apihz.cn/api/ip/chaapi.php'

    async def baidu(self, ip=''):
        """
        baidu ip: 5000次/日 并发3次/秒
        """
        params = {
            'ak': self.bd_key,
            'ip': ip,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bd_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        address_detail = data.get('content', {}).get('address_detail', {})
                        text = address_detail.get('province', '') + address_detail.get('city', '')
                        return text
                    else:
                        logger.error(f'Failed to get baidu ip, status code: {response.status}')
                        return ''
        except Exception as e:
            logger.error(f'Failed to get baidu ip, error: {e}')
            return ''

    async def gaode(self, ip=''):
        """
        gaode ip: 5000次/日 并发3次/秒
        """
        params = {
            'key': self.gd_key,
            'ip': ip,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.gd_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data.get('province', '') + data.get('city', '')
                        return text
                    else:
                        logger.error(f'Failed to get gaode ip, status code: {response.status}')
                        return ''
        except Exception as e:
            logger.error(f'Failed to get  gaode ip, error: {e}')
            return ''

    async def apihz1(self, ip=''):
        params = {
            'id': self.hz_id,
            'key': self.hz_key,
            'ip': ip,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.hz1_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data.get('provinces', '') + data.get('city', '')
                        return text
                    else:
                        logger.error(f'Failed to get apihz2 ip, status code: {response.status}')
                        return ''
        except Exception as e:
            logger.error(f'Failed to get apihz2 ip, error: {e}')
            return ''

    async def apihz2(self, ip=''):
        params = {
            'id': self.hz_id,
            'key': self.hz_key,
            'ip': ip,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.hz2_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data.get('sheng', '') + data.get('shi', '')
                        return text
                    else:
                        logger.error(f'Failed to get apihz1 ip, status code: {response.status}')
                        return ''
        except Exception as e:
            logger.error(f'Failed to get apihz1 ip, error: {e}')
            return ''

    async def get_location(self, ip=''):
        logger.info(f'Getting location of {ip}')
        if ip in ['127.0.0.1', 'localhost', '0.0.0.0']:
            return ''
        cache_key = f'ip-loc:{ip}'
        cached_location = await get_cache(cache_key)
        if cached_location is not None:
            logger.info(f'Returning cached location for {ip}: {cached_location}')
            return cached_location

        methods = [self.baidu, self.gaode, self.apihz1, self.apihz2]
        for method in methods:
            location = await method(ip)
            if location:
                await set_cache(cache_key, location, ttl=604800)  # 缓存一周
                return location
        return ''


ip2loc = IP2Location()
