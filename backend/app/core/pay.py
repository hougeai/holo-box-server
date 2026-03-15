import os
import json
import asyncio
import random

# import traceback
from datetime import datetime
from typing import Dict, Any

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


class PaymentService:
    def __init__(self):
        self.alipay_api = AlipayAPI()

    async def create_payment(self, amount: float, subject: str, out_trade_no: str = None) -> Dict[str, Any]:
        """创建支付订单（供外部调用的异步接口）"""
        return await asyncio.to_thread(self.alipay_api.create_order, amount, subject, out_trade_no)

    async def query_payment(self, out_trade_no: str) -> Dict[str, Any]:
        """查询订单状态（供外部调用的异步接口）"""
        return await asyncio.to_thread(self.alipay_api.query_order, out_trade_no)


# 创建支付服务实例
payment_service = PaymentService()
