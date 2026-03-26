import os
import json
import time
import base64
import asyncio
import random
import requests
import subprocess

from datetime import datetime
from typing import Dict, Any, Optional

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
from alipay.aop.api.request.AlipayTradeCloseRequest import AlipayTradeCloseRequest
from alipay.aop.api.request.AlipayTradeCancelRequest import AlipayTradeCancelRequest
from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.domain.AlipayTradeCloseModel import AlipayTradeCloseModel
from alipay.aop.api.domain.AlipayTradeCancelModel import AlipayTradeCancelModel
from alipay.aop.api.response.AlipayTradePayResponse import AlipayTradePayResponse
from alipay.aop.api.util.SignatureUtils import verify_with_rsa

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.Cipher import AES

from .config import settings
from .log import logger


class AlipayAPI:
    def __init__(self):
        self.client = self._init_client()

    def _init_client(self):
        """初始化支付宝客户端"""
        cfg = AlipayClientConfig()
        cfg.server_url = settings.ALIPAY_SERVER_URL
        cfg.app_id = settings.ALIPAY_APP_ID
        if not os.path.exists(settings.ALIPAY_APP_PRIVATE_KEY) or not os.path.exists(settings.ALIPAY_PUBLIC_KEY):
            raise FileNotFoundError(
                f'未找到支付宝密钥文件: {settings.ALIPAY_APP_PRIVATE_KEY} or {settings.ALIPAY_PUBLIC_KEY}'
            )
        with open(settings.ALIPAY_APP_PRIVATE_KEY, 'r') as f:
            cfg.app_private_key = f.read()
        with open(settings.ALIPAY_PUBLIC_KEY, 'r') as f:
            cfg.alipay_public_key = f.read()
        self.alipay_public_key = cfg.alipay_public_key
        # 调试密钥
        logger.info(f'支付宝配置: server_url={cfg.server_url}, app_id={cfg.app_id}')
        logger.info(f'私钥长度: {len(cfg.app_private_key)}')
        logger.info(f'公钥长度: {len(cfg.alipay_public_key)}')
        return DefaultAlipayClient(cfg)

    def verify_notification(self, data: Dict[str, str]) -> bool:
        """验证支付宝异步通知签名"""
        # 获取签名和签名类型
        sign = data.get('sign')
        if not sign:
            logger.error('通知数据中缺少签名')
            return False
        # 复制数据并移除签名相关字段
        cleaned_data = data.copy()
        cleaned_data.pop('sign', None)
        cleaned_data.pop('sign_type', None)
        # 按照支付宝要求排序参数
        sorted_items = sorted(cleaned_data.items(), key=lambda x: x[0])
        # 构造待签名字符串
        sign_content = '&'.join('{}={}'.format(k, v) for k, v in sorted_items if v != '')
        try:
            # 验证签名
            return verify_with_rsa(self.alipay_public_key, sign_content.encode('utf-8'), sign)
        except Exception as e:
            logger.error(f'验证支付宝签名时出错: {e}')
            return False

    def _send_request(self, request) -> Dict[str, Any]:
        """发送支付宝请求并解析响应"""
        response_content = None
        try:
            response_content = self.client.execute(request)
        except Exception as e:
            # logger.error(traceback.format_exc())
            logger.error(f'支付宝请求执行失败: {e}')
            return {'success': False, 'error': str(e)}

        if not response_content:
            logger.error('支付宝请求执行失败: 无响应内容')
            return {'success': False, 'error': 'failed execute'}

        response = AlipayTradePayResponse()
        response.parse_response_content(response_content)

        if response.is_success():
            # 如果业务成功，返回响应数据
            try:
                data = json.loads(response.body)
                return {'success': True, 'data': data}
            except json.JSONDecodeError as e:
                logger.error(f'解析支付宝响应失败: {e}')
                return {'success': False, 'error': response.body}
        else:
            # 如果业务失败，返回错误信息
            error_info = json.dumps(
                {'code': response.code, 'msg': response.msg, 'sub_code': response.sub_code, 'sub_msg': response.sub_msg}
            )
            logger.error(f'支付宝业务失败: {error_info}')
            return {'success': False, 'error': error_info}

    def create_order(self, amount: float, subject: str, out_trade_no: str = None) -> Dict[str, Any]:
        """创建支付订单"""
        if not out_trade_no:
            out_trade_no = self._generate_out_trade_no()

        model = AlipayTradePrecreateModel()
        model.out_trade_no = out_trade_no
        model.total_amount = str(amount)
        model.subject = subject

        request = AlipayTradePrecreateRequest(biz_model=model)
        # 如果配置了回调URL
        if settings.ALIPAY_NOTIFY_URL:
            request.notify_url = settings.ALIPAY_NOTIFY_URL
        result = self._send_request(request)

        if result['success']:
            logger.info(f'创建订单成功: {out_trade_no}')
        else:
            logger.error(f'创建订单失败: {result.get("error")}')

        return result

    def query_order(self, out_trade_no: str) -> Dict[str, Any]:
        """查询订单状态"""
        model = AlipayTradeQueryModel()
        model.out_trade_no = out_trade_no

        request = AlipayTradeQueryRequest(biz_model=model)
        result = self._send_request(request)

        if result['success']:
            logger.info(f'查询订单成功: {out_trade_no} {result.get("data")}')
        else:
            logger.error(f'查询订单失败: {result.get("error")}')

        return result

    def close_order(self, out_trade_no: str) -> Dict[str, Any]:
        """关闭订单"""
        model = AlipayTradeCloseModel()
        model.out_trade_no = out_trade_no

        request = AlipayTradeCloseRequest(biz_model=model)
        result = self._send_request(request)

        if result['success']:
            logger.info(f'关闭订单成功: {out_trade_no}')
        else:
            logger.error(f'关闭订单失败: {result.get("error")}')

        return result

    def cancel_order(self, out_trade_no: str) -> Dict[str, Any]:
        """撤销订单"""
        model = AlipayTradeCancelModel()
        model.out_trade_no = out_trade_no

        request = AlipayTradeCancelRequest(biz_model=model)
        result = self._send_request(request)

        if result['success']:
            logger.info(f'撤销订单成功: {out_trade_no}')
        else:
            logger.error(f'撤销订单失败: {result.get("error")}')

        return result

    def _generate_out_trade_no(self) -> str:
        """生成商户订单号"""
        return datetime.now().strftime('%Y%m%d%H%M%S%f') + f'{random.randint(1000, 9999):04d}'


class WXPayAPI:
    """微信支付 V3 API"""

    def __init__(self):
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_v3_key = settings.WECHAT_API_V3_KEY
        self.cert_path = settings.WECHAT_MCH_CERT
        self.key_path = settings.WECHAT_MCH_KEY
        self.platform_cert_path = settings.WECHAT_PLATFORM_CERT
        self.notify_url = settings.WECHAT_NOTIFY_URL
        self.appid = settings.MP_APPID
        self.base_url = 'https://api.mch.weixin.qq.com'

        # 验证配置
        if not all([self.mch_id, self.api_v3_key, self.cert_path, self.key_path]):
            raise ValueError('微信支付配置不完整，请检查环境变量')

        # 验证证书文件存在
        if not os.path.exists(self.cert_path):
            raise FileNotFoundError(f'商户证书不存在: {self.cert_path}')
        if not os.path.exists(self.key_path):
            raise FileNotFoundError(f'商户私钥不存在: {self.key_path}')

        # 获取证书序列号
        try:
            result = subprocess.run(
                ['openssl', 'x509', '-in', self.cert_path, '-noout', '-serial'],
                capture_output=True,
                text=True,
                check=True,
            )
            # 序列号格式: serial=75CC581567F7482701BBB6C2CA323654AE5663B3
            self.cert_serial = result.stdout.strip().split('=')[1]
        except Exception as e:
            logger.error(f'获取证书序列号失败: {e}')
            raise ValueError('获取证书序列号失败')

        logger.info(f'微信支付配置: mch_id={self.mch_id}, appid={self.appid}, cert_serial={self.cert_serial}')

    def _get_sign(self, method: str, url: str, timestamp: str, nonce_str: str, body: str = '') -> str:
        """生成签名"""
        # 构造签名串
        message = f'{method}\n{url}\n{timestamp}\n{nonce_str}\n{body}\n'
        # 读取私钥
        with open(self.key_path, 'r') as f:
            private_key = RSA.import_key(f.read())
        # 计算签名
        signer = PKCS1_v1_5.new(private_key)
        hash_obj = SHA256.new(message.encode('utf-8'))
        signature = base64.b64encode(signer.sign(hash_obj)).decode('utf-8')
        return signature

    def _get_auth_string(self, method: str, url: str, body: str = '') -> str:
        """生成 Authorization 头"""
        timestamp = str(int(time.time()))
        nonce_str = self._generate_nonce()
        signature = self._get_sign(method, url, timestamp, nonce_str, body)
        auth = f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce_str}",timestamp="{timestamp}",serial_no="{self.cert_serial}",signature="{signature}"'
        return auth

    def _generate_nonce(self) -> str:
        """生成随机字符串"""
        import random
        import string

        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def _request(self, method: str, url: str, body: str = None, need_cert: bool = True) -> Dict[str, Any]:
        """发送请求"""
        # 拼接完整 URL（用于实际请求，但签名只用路径）
        full_url = f'{self.base_url}{url}'

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        try:
            if method in ['POST', 'PUT', 'DELETE']:
                headers['Authorization'] = self._get_auth_string(method, url, body or '')
            else:
                headers['Authorization'] = self._get_auth_string(method, url)

            cert = (self.cert_path, self.key_path) if need_cert else None

            response = requests.request(
                method=method,
                url=full_url,
                data=body.encode('utf-8') if body else None,
                headers=headers,
                cert=cert,
                timeout=30,
            )

            logger.info(f'微信支付请求: {method} {url}, 状态码: {response.status_code}')

            try:
                data = response.json()
                logger.info(f'微信支付响应: {data}')
            except json.JSONDecodeError:
                return {'success': False, 'error': response.text, 'status_code': response.status_code}

            if response.status_code in [200, 204]:
                return {'success': True, 'data': data}
            else:
                return {'success': False, 'error': data.get('message', data), 'code': data.get('code')}

        except Exception as e:
            logger.error(f'微信支付请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_order(self, amount: float, description: str, out_trade_no: str, openid: str) -> Dict[str, Any]:
        """统一下单"""
        url = '/v3/pay/transactions/jsapi'

        # 注意：金额单位是分
        total = int(amount * 100)

        params = {
            'appid': self.appid,
            'mchid': self.mch_id,
            'description': description,
            'out_trade_no': out_trade_no,
            'notify_url': self.notify_url,
            'amount': {'total': total, 'currency': 'CNY'},
            'payer': {'openid': openid},
        }

        body = json.dumps(params, ensure_ascii=False)
        result = self._request('POST', url, body)

        if result['success']:
            # 返回调起支付需要的参数
            prepay_id = result['data'].get('prepay_id')
            if prepay_id:
                # 生成签名返回给小程序
                pay_params = self._get_jsapi_params(prepay_id)
                return {'success': True, 'data': pay_params, 'prepay_id': prepay_id}

        return result

    def _get_jsapi_params(self, prepay_id: str) -> Dict[str, Any]:
        """生成小程序调起支付的参数"""
        timestamp = str(int(time.time()))
        nonce_str = self._generate_nonce()

        # 签名顺序：appid\ntimestamp\nnoncestr\npackage\n
        # package 格式是 prepay_id=xxx
        package = f'prepay_id={prepay_id}'
        message = f'{self.appid}\n{timestamp}\n{nonce_str}\n{package}\n'

        with open(self.key_path, 'r') as f:
            private_key = RSA.import_key(f.read())

        signer = PKCS1_v1_5.new(private_key)
        hash_obj = SHA256.new(message.encode('utf-8'))
        signature = base64.b64encode(signer.sign(hash_obj)).decode('utf-8')

        return {
            'appId': self.appid,
            'timeStamp': timestamp,
            'nonceStr': nonce_str,
            'package': package,
            'signType': 'RSA',
            'paySign': signature,
        }

    def query_order(self, out_trade_no: str) -> Dict[str, Any]:
        """查询订单"""
        url = f'/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={self.mch_id}'
        return self._request('GET', url)

    def close_order(self, out_trade_no: str) -> Dict[str, Any]:
        """关闭订单"""
        url = f'/v3/pay/transactions/out-trade-no/{out_trade_no}/close'
        params = {'mchid': self.mch_id}
        body = json.dumps(params)
        return self._request('POST', url, body)

    def refund(self, out_trade_no: str, out_refund_no: str, amount: float, reason: str = '') -> Dict[str, Any]:
        """退款"""
        url = '/v3/refund/domestic/refunds'

        refund_amount = int(amount * 100)

        params = {
            'out_trade_no': out_trade_no,
            'out_refund_no': out_refund_no,
            'reason': reason,
            'notify_url': self.notify_url,
            'amount': {'refund': refund_amount, 'total': refund_amount, 'currency': 'CNY'},
        }

        body = json.dumps(params, ensure_ascii=False)
        return self._request('POST', url, body)

    def query_refund(self, out_refund_no: str) -> Dict[str, Any]:
        """查询退款"""
        url = f'/v3/refund/domestic/refunds/{out_refund_no}'
        return self._request('GET', url)

    def verify_callback(self, timestamp: str, nonce_str: str, body: str, signature: str, serial_no: str) -> bool:
        """验证回调签名"""
        try:
            # 检查时间戳是否过期（5分钟内）
            try:
                current_time = int(time.time())
                callback_time = int(timestamp)
            except ValueError:
                logger.error(f'微信支付回调时间戳无效: {timestamp}')
                return False

            if abs(current_time - callback_time) > 300:  # 5分钟 = 300秒
                logger.error(f'微信支付回调时间戳已过期: {timestamp}')
                return False

            # 构造签名串（注意：最后有换行符）
            message = f'{timestamp}\n{nonce_str}\n{body}\n'

            # 读取平台证书
            if not os.path.exists(self.platform_cert_path):
                logger.error(f'平台证书不存在: {self.platform_cert_path}')
                return False

            with open(self.platform_cert_path, 'r') as f:
                public_key = RSA.import_key(f.read())

            # 验证签名
            verifier = PKCS1_v1_5.new(public_key)
            hash_obj = SHA256.new(message.encode('utf-8'))

            try:
                verifier.verify(hash_obj, base64.b64decode(signature))
                return True
            except ValueError:
                logger.error('微信支付回调签名验证失败')
                return False

        except Exception as e:
            logger.error(f'验证回调签名异常: {e}')
            return False

    def decrypt_callback(self, ciphertext: str, nonce: str, associated_data: str) -> Optional[Dict]:
        """解密回调内容（使用 AES-256-GCM）"""
        try:
            # APIv3 密钥是 32 字节
            key = self.api_v3_key.encode('utf-8')
            nonce_bytes = nonce.encode('utf-8')
            associated_data_bytes = associated_data.encode('utf-8') if associated_data else b''

            # Base64 解码
            ciphertext_bytes = base64.b64decode(ciphertext)

            # AES-256-GCM 解密
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce_bytes)
            if associated_data_bytes:
                cipher.update(associated_data_bytes)

            # 解密（最后16字节是 auth tag）
            plaintext = cipher.decrypt_and_verify(ciphertext_bytes[:-16], ciphertext_bytes[-16:])

            # 解析 JSON
            result = json.loads(plaintext.decode('utf-8'))
            return result

        except Exception as e:
            logger.error(f'解密回调内容失败: {e}')
            return None


class PaymentService:
    def __init__(self):
        self.alipay_api = AlipayAPI()
        self.wxpay_api = WXPayAPI()

    async def create_payment(self, amount: float, subject: str, out_trade_no: str = None) -> Dict[str, Any]:
        """创建支付宝支付订单"""
        return await asyncio.to_thread(self.alipay_api.create_order, amount, subject, out_trade_no)

    async def query_payment(self, out_trade_no: str) -> Dict[str, Any]:
        """查询支付宝订单状态"""
        return await asyncio.to_thread(self.alipay_api.query_order, out_trade_no)

    # ====== 微信支付接口 ======

    async def create_wx_payment(
        self, amount: float, description: str, out_trade_no: str, openid: str
    ) -> Dict[str, Any]:
        """创建微信支付订单"""
        return await asyncio.to_thread(self.wxpay_api.create_order, amount, description, out_trade_no, openid)

    async def query_wx_payment(self, out_trade_no: str) -> Dict[str, Any]:
        """查询微信支付订单"""
        return await asyncio.to_thread(self.wxpay_api.query_order, out_trade_no)

    async def close_wx_payment(self, out_trade_no: str) -> Dict[str, Any]:
        """关闭微信支付订单"""
        return await asyncio.to_thread(self.wxpay_api.close_order, out_trade_no)

    async def refund_wx_payment(
        self, out_trade_no: str, out_refund_no: str, amount: float, reason: str = ''
    ) -> Dict[str, Any]:
        """微信支付退款"""
        return await asyncio.to_thread(self.wxpay_api.refund, out_trade_no, out_refund_no, amount, reason)

    async def query_wx_refund(self, out_refund_no: str) -> Dict[str, Any]:
        """查询微信退款状态"""
        return await asyncio.to_thread(self.wxpay_api.query_refund, out_refund_no)

    def verify_wxpay_notification(self, headers, body: str) -> bool:
        """验证微信支付回调"""
        # 微信支付回调头使用大写字母，如 Wechatpay-Timestamp
        # 但 FastAPI 的 headers 是 case-insensitive 的
        timestamp = headers.get('Wechatpay-Timestamp') or headers.get('wechatpay-timestamp') or ''
        nonce_str = headers.get('Wechatpay-Nonce') or headers.get('wechatpay-nonce') or ''
        signature = headers.get('Wechatpay-Signature') or headers.get('wechatpay-signature') or ''
        serial_no = headers.get('Wechatpay-Serial') or headers.get('wechatpay-serial') or ''

        logger.info(
            f'微信回调头: timestamp={timestamp}, nonce_str={nonce_str}, signature={signature[:20] if signature else ""}..., serial_no={serial_no}'
        )

        # 检查参数是否为空
        if not timestamp or not nonce_str or not signature:
            logger.error(f'回调头参数不完整: timestamp={timestamp}, nonce_str={nonce_str}, signature={signature}')
            return False

        return self.wxpay_api.verify_callback(timestamp, nonce_str, body, signature, serial_no)

    def parse_wxpay_notification(self, body: str) -> Optional[Dict]:
        """解析微信支付回调"""
        try:
            data = json.loads(body)
            # 从 resource 字段中获取加密数据
            resource = data.get('resource', {})
            ciphertext = resource.get('ciphertext', '')
            nonce = resource.get('nonce', '')
            associated_data = resource.get('associated_data', '')

            if not ciphertext:
                logger.error('通知内容缺少 ciphertext')
                return None

            return self.wxpay_api.decrypt_callback(ciphertext, nonce, associated_data)
        except Exception as e:
            logger.error(f'解析通知失败: {e}')
            return None


# 创建支付服务实例
payment_service = PaymentService()
